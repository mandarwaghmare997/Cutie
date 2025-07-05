from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime

from src.models.user import User, db
from src.models.assessment import Assessment, AssessmentFile
from src.utils.validation import validate_file_upload

file_bp = Blueprint('file', __name__)

def get_file_extension(filename):
    """Get file extension from filename"""
    return '.' + filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

def generate_stored_filename(original_filename):
    """Generate a unique stored filename"""
    file_id = str(uuid.uuid4())
    extension = get_file_extension(original_filename)
    return f"{file_id}{extension}"

@file_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    """Upload evidence file for assessment"""
    try:
        current_user_id = get_jwt_identity()
        
        # Check if file is present in request
        if 'file' not in request.files:
            return jsonify({
                'error': 'no_file',
                'message': 'No file provided in request'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'error': 'no_filename',
                'message': 'No file selected'
            }), 400
        
        # Get form data
        assessment_id = request.form.get('assessmentId')
        control_id = request.form.get('controlId')
        stage = request.form.get('stage')
        description = request.form.get('description', '')
        
        if not assessment_id:
            return jsonify({
                'error': 'missing_assessment_id',
                'message': 'Assessment ID is required'
            }), 400
        
        # Verify assessment exists and belongs to user
        assessment = Assessment.query.filter_by(
            id=assessment_id,
            user_id=current_user_id
        ).first()
        
        if not assessment:
            return jsonify({
                'error': 'assessment_not_found',
                'message': 'Assessment not found or access denied'
            }), 404
        
        # Validate file
        file_data = {
            'filename': file.filename,
            'size': len(file.read()),
            'content_type': file.content_type
        }
        file.seek(0)  # Reset file pointer after reading for size
        
        validation_result = validate_file_upload(file_data)
        if not validation_result['is_valid']:
            return jsonify({
                'error': 'file_validation_error',
                'message': 'File validation failed',
                'details': validation_result['errors']
            }), 400
        
        # Generate secure filename and path
        original_filename = secure_filename(file.filename)
        stored_filename = generate_stored_filename(original_filename)
        
        # Create upload directory if it doesn't exist
        upload_dir = current_app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        # Create subdirectory for the assessment
        assessment_dir = os.path.join(upload_dir, assessment_id)
        if not os.path.exists(assessment_dir):
            os.makedirs(assessment_dir)
        
        file_path = os.path.join(assessment_dir, stored_filename)
        
        # Save file
        file.save(file_path)
        
        # Create database record
        assessment_file = AssessmentFile(
            assessment_id=assessment_id,
            user_id=current_user_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_path=file_path,
            file_size=file_data['size'],
            file_type=get_file_extension(original_filename),
            mime_type=file.content_type or 'application/octet-stream',
            control_id=control_id,
            stage=stage,
            description=description
        )
        
        # Mark as clean for now (in production, would integrate virus scanning)
        assessment_file.mark_as_clean()
        
        db.session.add(assessment_file)
        db.session.commit()
        
        return jsonify({
            'fileId': assessment_file.id,
            'fileName': original_filename,
            'fileSize': file_data['size'],
            'fileType': assessment_file.file_type,
            'uploadDate': assessment_file.uploaded_at.isoformat(),
            'scanStatus': assessment_file.scan_status,
            'downloadUrl': f'/api/files/{assessment_file.id}/download'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"File upload error: {str(e)}")
        return jsonify({
            'error': 'internal_error',
            'message': 'An error occurred while uploading the file'
        }), 500

@file_bp.route('/<file_id>/download', methods=['GET'])
@jwt_required()
def download_file(file_id):
    """Download an uploaded file"""
    try:
        current_user_id = get_jwt_identity()
        
        # Find file record
        file_record = AssessmentFile.query.filter_by(id=file_id).first()
        
        if not file_record:
            return jsonify({
                'error': 'file_not_found',
                'message': 'File not found'
            }), 404
        
        # Check if user has access to this file
        assessment = Assessment.query.filter_by(
            id=file_record.assessment_id,
            user_id=current_user_id
        ).first()
        
        if not assessment:
            return jsonify({
                'error': 'access_denied',
                'message': 'Access denied to this file'
            }), 403
        
        # Check if file exists on disk
        if not os.path.exists(file_record.file_path):
            return jsonify({
                'error': 'file_not_found_disk',
                'message': 'File not found on disk'
            }), 404
        
        # Check scan status
        if file_record.scan_status == 'infected':
            return jsonify({
                'error': 'file_infected',
                'message': 'File is infected and cannot be downloaded'
            }), 403
        
        return send_file(
            file_record.file_path,
            as_attachment=True,
            download_name=file_record.original_filename,
            mimetype=file_record.mime_type
        )
        
    except Exception as e:
        current_app.logger.error(f"File download error: {str(e)}")
        return jsonify({
            'error': 'internal_error',
            'message': 'An error occurred while downloading the file'
        }), 500

@file_bp.route('/<file_id>', methods=['GET'])
@jwt_required()
def get_file_info(file_id):
    """Get file information"""
    try:
        current_user_id = get_jwt_identity()
        
        # Find file record
        file_record = AssessmentFile.query.filter_by(id=file_id).first()
        
        if not file_record:
            return jsonify({
                'error': 'file_not_found',
                'message': 'File not found'
            }), 404
        
        # Check if user has access to this file
        assessment = Assessment.query.filter_by(
            id=file_record.assessment_id,
            user_id=current_user_id
        ).first()
        
        if not assessment:
            return jsonify({
                'error': 'access_denied',
                'message': 'Access denied to this file'
            }), 403
        
        return jsonify(file_record.to_dict()), 200
        
    except Exception as e:
        current_app.logger.error(f"Get file info error: {str(e)}")
        return jsonify({
            'error': 'internal_error',
            'message': 'An error occurred while fetching file information'
        }), 500

@file_bp.route('/<file_id>', methods=['DELETE'])
@jwt_required()
def delete_file(file_id):
    """Delete an uploaded file"""
    try:
        current_user_id = get_jwt_identity()
        
        # Find file record
        file_record = AssessmentFile.query.filter_by(id=file_id).first()
        
        if not file_record:
            return jsonify({
                'error': 'file_not_found',
                'message': 'File not found'
            }), 404
        
        # Check if user has access to this file
        assessment = Assessment.query.filter_by(
            id=file_record.assessment_id,
            user_id=current_user_id
        ).first()
        
        if not assessment:
            return jsonify({
                'error': 'access_denied',
                'message': 'Access denied to this file'
            }), 403
        
        # Delete file from disk
        if os.path.exists(file_record.file_path):
            try:
                os.remove(file_record.file_path)
            except OSError as e:
                current_app.logger.warning(f"Could not delete file from disk: {str(e)}")
        
        # Delete database record
        db.session.delete(file_record)
        db.session.commit()
        
        return jsonify({
            'message': 'File deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete file error: {str(e)}")
        return jsonify({
            'error': 'internal_error',
            'message': 'An error occurred while deleting the file'
        }), 500

@file_bp.route('/assessment/<assessment_id>', methods=['GET'])
@jwt_required()
def get_assessment_files(assessment_id):
    """Get all files for an assessment"""
    try:
        current_user_id = get_jwt_identity()
        
        # Verify assessment exists and belongs to user
        assessment = Assessment.query.filter_by(
            id=assessment_id,
            user_id=current_user_id
        ).first()
        
        if not assessment:
            return jsonify({
                'error': 'assessment_not_found',
                'message': 'Assessment not found or access denied'
            }), 404
        
        # Get query parameters
        control_id = request.args.get('control_id')
        stage = request.args.get('stage')
        
        # Build query
        query = AssessmentFile.query.filter_by(assessment_id=assessment_id)
        
        if control_id:
            query = query.filter_by(control_id=control_id)
        
        if stage:
            query = query.filter_by(stage=stage)
        
        files = query.order_by(AssessmentFile.uploaded_at.desc()).all()
        
        return jsonify({
            'files': [file.to_dict() for file in files],
            'total': len(files)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get assessment files error: {str(e)}")
        return jsonify({
            'error': 'internal_error',
            'message': 'An error occurred while fetching assessment files'
        }), 500

@file_bp.route('/<file_id>/metadata', methods=['PUT'])
@jwt_required()
def update_file_metadata(file_id):
    """Update file metadata"""
    try:
        current_user_id = get_jwt_identity()
        
        # Find file record
        file_record = AssessmentFile.query.filter_by(id=file_id).first()
        
        if not file_record:
            return jsonify({
                'error': 'file_not_found',
                'message': 'File not found'
            }), 404
        
        # Check if user has access to this file
        assessment = Assessment.query.filter_by(
            id=file_record.assessment_id,
            user_id=current_user_id
        ).first()
        
        if not assessment:
            return jsonify({
                'error': 'access_denied',
                'message': 'Access denied to this file'
            }), 403
        
        data = request.get_json()
        
        # Update allowed fields
        if 'description' in data:
            file_record.description = data['description']
        
        if 'controlId' in data:
            file_record.control_id = data['controlId']
        
        if 'stage' in data:
            file_record.stage = data['stage']
        
        db.session.commit()
        
        return jsonify({
            'message': 'File metadata updated successfully',
            'file': file_record.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update file metadata error: {str(e)}")
        return jsonify({
            'error': 'internal_error',
            'message': 'An error occurred while updating file metadata'
        }), 500

