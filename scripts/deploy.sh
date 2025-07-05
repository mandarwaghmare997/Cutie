#!/bin/bash

# Qryti Platform Deployment Script
# This script helps deploy the Qryti platform to AWS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="production"
REGION="us-east-1"
STACK_NAME=""
ADMIN_EMAIL=""

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command_exists aws; then
        print_error "AWS CLI is not installed. Please install it first."
        echo "Visit: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity >/dev/null 2>&1; then
        print_error "AWS credentials not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    # Check if we're in the right directory
    if [ ! -f "deployment/aws/cloudformation-template.yaml" ]; then
        print_error "CloudFormation template not found. Please run this script from the project root."
        exit 1
    fi
    
    print_success "Prerequisites check passed!"
}

# Function to validate parameters
validate_parameters() {
    if [ -z "$ADMIN_EMAIL" ]; then
        print_error "Admin email is required. Use --admin-email parameter."
        exit 1
    fi
    
    # Validate email format
    if [[ ! "$ADMIN_EMAIL" =~ ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$ ]]; then
        print_error "Invalid email format: $ADMIN_EMAIL"
        exit 1
    fi
    
    if [ -z "$STACK_NAME" ]; then
        STACK_NAME="qryti-platform-$ENVIRONMENT"
    fi
    
    print_status "Deployment parameters:"
    echo "  Environment: $ENVIRONMENT"
    echo "  Region: $REGION"
    echo "  Stack Name: $STACK_NAME"
    echo "  Admin Email: $ADMIN_EMAIL"
}

# Function to create S3 bucket for Lambda deployment
create_deployment_bucket() {
    local bucket_name="qryti-deployment-artifacts-$(aws sts get-caller-identity --query Account --output text)"
    
    print_status "Creating deployment bucket: $bucket_name"
    
    if aws s3 ls "s3://$bucket_name" >/dev/null 2>&1; then
        print_warning "Bucket $bucket_name already exists"
    else
        aws s3 mb "s3://$bucket_name" --region "$REGION"
        print_success "Created deployment bucket: $bucket_name"
    fi
    
    echo "$bucket_name"
}

# Function to package Lambda function
package_lambda() {
    local bucket_name="$1"
    
    print_status "Packaging Lambda function..."
    
    # Create temporary directory
    local temp_dir=$(mktemp -d)
    
    # Install dependencies
    print_status "Installing Python dependencies..."
    pip install -r requirements.txt -t "$temp_dir" --quiet
    
    # Copy source code
    cp -r src/* "$temp_dir/"
    
    # Create ZIP package
    cd "$temp_dir"
    zip -r ../qryti-api.zip . >/dev/null
    cd - >/dev/null
    
    # Upload to S3
    print_status "Uploading Lambda package to S3..."
    aws s3 cp "$temp_dir/../qryti-api.zip" "s3://$bucket_name/lambda/qryti-api.zip"
    
    # Clean up
    rm -rf "$temp_dir" "$temp_dir/../qryti-api.zip"
    
    print_success "Lambda function packaged and uploaded!"
    echo "s3://$bucket_name/lambda/qryti-api.zip"
}

# Function to deploy CloudFormation stack
deploy_stack() {
    local bucket_name="$1"
    local lambda_s3_key="lambda/qryti-api.zip"
    
    print_status "Deploying CloudFormation stack: $STACK_NAME"
    
    # Generate secure secrets if not provided
    if [ -z "$JWT_SECRET" ]; then
        JWT_SECRET=$(openssl rand -base64 32)
        print_status "Generated JWT secret"
    fi
    
    if [ -z "$ENCRYPTION_KEY" ]; then
        ENCRYPTION_KEY=$(openssl rand -base64 32)
        print_status "Generated encryption key"
    fi
    
    # Deploy stack
    aws cloudformation deploy \
        --template-file deployment/aws/cloudformation-template.yaml \
        --stack-name "$STACK_NAME" \
        --parameter-overrides \
            Environment="$ENVIRONMENT" \
            AdminEmail="$ADMIN_EMAIL" \
            JWTSecret="$JWT_SECRET" \
            EncryptionKey="$ENCRYPTION_KEY" \
            LambdaS3Bucket="$bucket_name" \
            LambdaS3Key="$lambda_s3_key" \
        --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
        --region "$REGION" \
        --no-fail-on-empty-changeset
    
    print_success "CloudFormation stack deployed successfully!"
}

# Function to deploy frontend
deploy_frontend() {
    print_status "Deploying frontend..."
    
    # Get S3 bucket name from CloudFormation outputs
    local bucket_name=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucket`].OutputValue' \
        --output text)
    
    if [ "$bucket_name" = "None" ] || [ -z "$bucket_name" ]; then
        print_error "Could not get frontend bucket name from CloudFormation stack"
        exit 1
    fi
    
    # Create dist directory and copy static files
    mkdir -p dist
    cp -r src/static/* dist/
    
    # Upload to S3
    aws s3 sync dist/ "s3://$bucket_name" --delete --region "$REGION"
    
    # Get CloudFront distribution ID
    local distribution_id=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistribution`].OutputValue' \
        --output text)
    
    # Invalidate CloudFront cache
    if [ "$distribution_id" != "None" ] && [ -n "$distribution_id" ]; then
        print_status "Invalidating CloudFront cache..."
        aws cloudfront create-invalidation \
            --distribution-id "$distribution_id" \
            --paths "/*" >/dev/null
    fi
    
    # Clean up
    rm -rf dist/
    
    print_success "Frontend deployed successfully!"
}

# Function to get deployment URLs
get_deployment_urls() {
    print_status "Getting deployment URLs..."
    
    local frontend_url=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`FrontendUrl`].OutputValue' \
        --output text)
    
    local api_url=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
        --output text)
    
    echo ""
    print_success "🎉 Deployment completed successfully!"
    echo ""
    echo "📱 Access your Qryti platform:"
    echo "   Frontend: $frontend_url"
    echo "   API: $api_url"
    echo ""
    echo "🔧 Next steps:"
    echo "   1. Test the platform by visiting the frontend URL"
    echo "   2. Register a new user to test the complete flow"
    echo "   3. Check the admin dashboard"
    echo "   4. Monitor CloudWatch logs for any issues"
    echo ""
}

# Function to run health checks
run_health_checks() {
    print_status "Running health checks..."
    
    local frontend_url=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`FrontendUrl`].OutputValue' \
        --output text)
    
    # Test frontend
    if curl -f -s "$frontend_url" >/dev/null; then
        print_success "✅ Frontend is accessible"
    else
        print_warning "⚠️ Frontend health check failed"
    fi
    
    # Wait a moment for services to be ready
    sleep 5
    
    print_success "Health checks completed!"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --environment ENV     Deployment environment (default: production)"
    echo "  --region REGION       AWS region (default: us-east-1)"
    echo "  --stack-name NAME     CloudFormation stack name (default: qryti-platform-ENV)"
    echo "  --admin-email EMAIL   Administrator email address (required)"
    echo "  --jwt-secret SECRET   JWT secret key (auto-generated if not provided)"
    echo "  --encryption-key KEY  Encryption key (auto-generated if not provided)"
    echo "  --help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --admin-email admin@example.com"
    echo "  $0 --environment staging --admin-email admin@example.com"
    echo "  $0 --region eu-west-1 --admin-email admin@example.com"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --stack-name)
            STACK_NAME="$2"
            shift 2
            ;;
        --admin-email)
            ADMIN_EMAIL="$2"
            shift 2
            ;;
        --jwt-secret)
            JWT_SECRET="$2"
            shift 2
            ;;
        --encryption-key)
            ENCRYPTION_KEY="$2"
            shift 2
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main deployment flow
main() {
    echo "🚀 Qryti Platform Deployment Script"
    echo "===================================="
    echo ""
    
    check_prerequisites
    validate_parameters
    
    echo ""
    read -p "Do you want to proceed with the deployment? (y/N): " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Deployment cancelled by user"
        exit 0
    fi
    
    echo ""
    print_status "Starting deployment process..."
    
    # Create deployment bucket and package Lambda
    bucket_name=$(create_deployment_bucket)
    package_lambda "$bucket_name"
    
    # Deploy infrastructure
    deploy_stack "$bucket_name"
    
    # Deploy frontend
    deploy_frontend
    
    # Run health checks
    run_health_checks
    
    # Show deployment URLs
    get_deployment_urls
}

# Run main function
main "$@"

