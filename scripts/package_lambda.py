#!/usr/bin/env python3
"""
Lambda Function Packaging Script for ISO 42001 Platform
Packages Python code and dependencies for AWS Lambda deployment
"""

import os
import sys
import shutil
import zipfile
import subprocess
from pathlib import Path

def create_lambda_package(function_name, source_dir, output_dir, requirements_file=None):
    """
    Create a deployment package for a Lambda function
    
    Args:
        function_name (str): Name of the Lambda function
        source_dir (str): Directory containing the source code
        output_dir (str): Directory to save the package
        requirements_file (str): Path to requirements.txt file
    """
    print(f"📦 Packaging {function_name}...")
    
    # Create temporary directory for packaging
    temp_dir = Path(f"temp_{function_name}")
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # Copy source code
        if os.path.isfile(source_dir):
            shutil.copy2(source_dir, temp_dir)
        else:
            shutil.copytree(source_dir, temp_dir / "src", dirs_exist_ok=True)
        
        # Install dependencies if requirements file exists
        if requirements_file and os.path.exists(requirements_file):
            print(f"  📋 Installing dependencies from {requirements_file}")
            subprocess.run([
                sys.executable, "-m", "pip", "install",
                "-r", requirements_file,
                "-t", str(temp_dir),
                "--no-deps"
            ], check=True)
        
        # Create ZIP package
        package_path = Path(output_dir) / f"{function_name}.zip"
        package_path.parent.mkdir(parents=True, exist_ok=True)
        
        with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arcname)
        
        print(f"  ✅ Package created: {package_path}")
        print(f"  📊 Package size: {package_path.stat().st_size / 1024 / 1024:.2f} MB")
        
    finally:
        # Clean up temporary directory
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

def create_api_lambda():
    """Create the main API Lambda function package"""
    print("🔧 Creating API Lambda package...")
    
    # Create a combined handler for the API
    api_handler = """
import json
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from main import app
from mangum import Mangum

# Create Lambda handler
handler = Mangum(app, lifespan="off")

def lambda_handler(event, context):
    \"\"\"AWS Lambda handler for the Flask application\"\"\"
    return handler(event, context)
"""
    
    # Write the handler file
    with open("lambda_api_handler.py", "w") as f:
        f.write(api_handler)
    
    # Create requirements for Lambda
    lambda_requirements = """
flask==2.3.3
flask-cors==4.0.0
flask-jwt-extended==4.5.3
bcrypt==4.0.1
boto3==1.28.62
python-dotenv==1.0.0
mangum==0.17.0
cryptography==41.0.7
reportlab==4.0.4
qrcode[pil]==7.4.2
pillow==10.0.1
"""
    
    with open("lambda_requirements.txt", "w") as f:
        f.write(lambda_requirements)
    
    create_lambda_package(
        "iso42001-api",
        "lambda_api_handler.py",
        "lambda-packages",
        "lambda_requirements.txt"
    )
    
    # Clean up temporary files
    os.remove("lambda_api_handler.py")
    os.remove("lambda_requirements.txt")

def create_auth_lambda():
    """Create the authentication Lambda function package"""
    print("🔐 Creating Auth Lambda package...")
    
    auth_handler = """
import json
import boto3
import bcrypt
import jwt
import os
from datetime import datetime, timedelta
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
ses = boto3.client('ses')

def lambda_handler(event, context):
    \"\"\"Handle authentication requests\"\"\"
    
    try:
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        body = json.loads(event.get('body', '{}'))
        
        if path == '/auth/register' and http_method == 'POST':
            return handle_register(body)
        elif path == '/auth/login' and http_method == 'POST':
            return handle_login(body)
        elif path == '/auth/verify-otp' and http_method == 'POST':
            return handle_verify_otp(body)
        else:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Not found'})
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def handle_register(data):
    \"\"\"Handle user registration\"\"\"
    # Implementation would go here
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'message': 'Registration successful'})
    }

def handle_login(data):
    \"\"\"Handle user login\"\"\"
    # Implementation would go here
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'message': 'Login successful'})
    }

def handle_verify_otp(data):
    \"\"\"Handle OTP verification\"\"\"
    # Implementation would go here
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'message': 'OTP verified'})
    }
"""
    
    with open("auth_handler.py", "w") as f:
        f.write(auth_handler)
    
    auth_requirements = """
boto3==1.28.62
bcrypt==4.0.1
PyJWT==2.8.0
"""
    
    with open("auth_requirements.txt", "w") as f:
        f.write(auth_requirements)
    
    create_lambda_package(
        "iso42001-auth",
        "auth_handler.py",
        "lambda-packages",
        "auth_requirements.txt"
    )
    
    # Clean up
    os.remove("auth_handler.py")
    os.remove("auth_requirements.txt")

def create_assessment_lambda():
    """Create the assessment Lambda function package"""
    print("📋 Creating Assessment Lambda package...")
    
    assessment_handler = """
import json
import boto3
import os
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    \"\"\"Handle assessment requests\"\"\"
    
    try:
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        body = json.loads(event.get('body', '{}'))
        
        if 'assessment' in path:
            if http_method == 'POST':
                return handle_create_assessment(body)
            elif http_method == 'GET':
                return handle_get_assessment(event)
            elif http_method == 'PUT':
                return handle_update_assessment(body)
        
        return {
            'statusCode': 404,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Not found'})
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def handle_create_assessment(data):
    \"\"\"Create new assessment\"\"\"
    # Implementation would go here
    return {
        'statusCode': 201,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'message': 'Assessment created'})
    }

def handle_get_assessment(event):
    \"\"\"Get assessment data\"\"\"
    # Implementation would go here
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'message': 'Assessment data'})
    }

def handle_update_assessment(data):
    \"\"\"Update assessment\"\"\"
    # Implementation would go here
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'message': 'Assessment updated'})
    }
"""
    
    with open("assessment_handler.py", "w") as f:
        f.write(assessment_handler)
    
    assessment_requirements = """
boto3==1.28.62
"""
    
    with open("assessment_requirements.txt", "w") as f:
        f.write(assessment_requirements)
    
    create_lambda_package(
        "iso42001-assessment",
        "assessment_handler.py",
        "lambda-packages",
        "assessment_requirements.txt"
    )
    
    # Clean up
    os.remove("assessment_handler.py")
    os.remove("assessment_requirements.txt")

def create_file_processor_lambda():
    """Create the file processor Lambda function package"""
    print("📁 Creating File Processor Lambda package...")
    
    file_processor_handler = """
import json
import boto3
import os
from urllib.parse import unquote_plus

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    \"\"\"Process uploaded files\"\"\"
    
    try:
        for record in event['Records']:
            bucket = record['s3']['bucket']['name']
            key = unquote_plus(record['s3']['object']['key'])
            
            # Process the uploaded file
            process_uploaded_file(bucket, key)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Files processed successfully'})
        }
        
    except Exception as e:
        print(f"Error processing files: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def process_uploaded_file(bucket, key):
    \"\"\"Process individual uploaded file\"\"\"
    
    # Get file metadata
    response = s3.head_object(Bucket=bucket, Key=key)
    file_size = response['ContentLength']
    content_type = response.get('ContentType', 'application/octet-stream')
    
    # Update file record in DynamoDB
    files_table = dynamodb.Table(os.environ['FILES_TABLE'])
    
    # Extract file ID from key (assuming format: user_id/assessment_id/file_id)
    parts = key.split('/')
    if len(parts) >= 3:
        file_id = parts[-1].split('.')[0]  # Remove extension
        
        files_table.update_item(
            Key={'file_id': file_id},
            UpdateExpression='SET file_size = :size, content_type = :type, is_processed = :processed',
            ExpressionAttributeValues={
                ':size': file_size,
                ':type': content_type,
                ':processed': True
            }
        )
    
    print(f"Processed file: {key} ({file_size} bytes)")
"""
    
    with open("file_processor_handler.py", "w") as f:
        f.write(file_processor_handler)
    
    file_processor_requirements = """
boto3==1.28.62
"""
    
    with open("file_processor_requirements.txt", "w") as f:
        f.write(file_processor_requirements)
    
    create_lambda_package(
        "iso42001-file-processor",
        "file_processor_handler.py",
        "lambda-packages",
        "file_processor_requirements.txt"
    )
    
    # Clean up
    os.remove("file_processor_handler.py")
    os.remove("file_processor_requirements.txt")

def main():
    """Main packaging function"""
    print("🚀 Starting Lambda function packaging...")
    
    # Create output directory
    os.makedirs("lambda-packages", exist_ok=True)
    
    # Package all Lambda functions
    create_api_lambda()
    create_auth_lambda()
    create_assessment_lambda()
    create_file_processor_lambda()
    
    print("\n✅ All Lambda packages created successfully!")
    print("\n📦 Package Summary:")
    
    # List all created packages
    for package in Path("lambda-packages").glob("*.zip"):
        size_mb = package.stat().st_size / 1024 / 1024
        print(f"  📄 {package.name}: {size_mb:.2f} MB")

if __name__ == "__main__":
    main()

