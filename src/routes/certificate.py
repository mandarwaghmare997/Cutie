from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
import tempfile
from datetime import datetime
from src.models.user import db, User
from src.models.assessment import Assessment
from src.utils.certificate_generator import generate_compliance_certificate

certificate_bp = Blueprint('certificate', __name__)

@certificate_bp.route('/generate/<int:assessment_id>', methods=['POST'])
@jwt_required()
def generate_certificate(assessment_id):
    """Generate a compliance certificate for a completed assessment"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get the assessment
        assessment = Assessment.query.filter_by(
            id=assessment_id,
            user_id=current_user_id
        ).first()
        
        if not assessment:
            return jsonify({'error': 'Assessment not found'}), 404
        
        # Check if assessment is completed and meets requirements
        if assessment.status != 'completed':
            return jsonify({'error': 'Assessment must be completed to generate certificate'}), 400
        
        if not assessment.final_score or assessment.final_score < 70:
            return jsonify({
                'error': 'Assessment score must be 70% or higher to generate certificate',
                'current_score': assessment.final_score
            }), 400
        
        # Prepare certificate data
        certificate_data = {
            'organization_name': assessment.organization_name,
            'ai_system_name': assessment.ai_system_name,
            'ai_system_description': assessment.ai_system_description,
            'final_score': assessment.final_score,
            'risk_level': assessment.risk_level,
            'industry': assessment.industry,
            'completion_date': assessment.completed_at.strftime('%B %d, %Y') if assessment.completed_at else datetime.now().strftime('%B %d, %Y'),
            'certificate_id': f'CERT-{assessment.id}-{datetime.now().strftime("%Y%m%d")}',
            'user_name': f'{user.first_name} {user.last_name}',
            'user_email': user.email,
            'assessment_id': assessment.id
        }
        
        # Create certificates directory if it doesn't exist
        certificates_dir = os.path.join(os.path.dirname(__file__), '..', 'certificates')
        os.makedirs(certificates_dir, exist_ok=True)
        
        # Generate the certificate
        certificate_path = generate_compliance_certificate(certificate_data, certificates_dir)
        
        # Update assessment with certificate information
        assessment.certificate_generated = True
        assessment.certificate_id = certificate_data['certificate_id']
        assessment.certificate_generated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Certificate generated successfully',
            'certificate_id': certificate_data['certificate_id'],
            'certificate_path': certificate_path,
            'download_url': f'/api/certificates/download/{assessment.id}'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to generate certificate: {str(e)}'}), 500

@certificate_bp.route('/download/<int:assessment_id>', methods=['GET'])
@jwt_required()
def download_certificate(assessment_id):
    """Download the certificate for an assessment"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get the assessment
        assessment = Assessment.query.filter_by(
            id=assessment_id,
            user_id=current_user_id
        ).first()
        
        if not assessment:
            return jsonify({'error': 'Assessment not found'}), 404
        
        if not assessment.certificate_generated or not assessment.certificate_id:
            return jsonify({'error': 'Certificate not generated for this assessment'}), 404
        
        # Find the certificate file
        certificates_dir = os.path.join(os.path.dirname(__file__), '..', 'certificates')
        
        # Look for certificate file with the assessment ID
        certificate_files = [f for f in os.listdir(certificates_dir) if f.startswith(f'ISO42001_Certificate_') and assessment.organization_name.replace(' ', '_') in f]
        
        if not certificate_files:
            # Certificate file not found, regenerate it
            user = User.query.get(current_user_id)
            certificate_data = {
                'organization_name': assessment.organization_name,
                'ai_system_name': assessment.ai_system_name,
                'ai_system_description': assessment.ai_system_description,
                'final_score': assessment.final_score,
                'risk_level': assessment.risk_level,
                'industry': assessment.industry,
                'completion_date': assessment.completed_at.strftime('%B %d, %Y') if assessment.completed_at else datetime.now().strftime('%B %d, %Y'),
                'certificate_id': assessment.certificate_id,
                'user_name': f'{user.first_name} {user.last_name}',
                'user_email': user.email,
                'assessment_id': assessment.id
            }
            
            certificate_path = generate_compliance_certificate(certificate_data, certificates_dir)
        else:
            certificate_path = os.path.join(certificates_dir, certificate_files[0])
        
        if not os.path.exists(certificate_path):
            return jsonify({'error': 'Certificate file not found'}), 404
        
        # Generate download filename
        download_filename = f"ISO42001_Certificate_{assessment.organization_name.replace(' ', '_')}_{assessment.certificate_id}.pdf"
        
        return send_file(
            certificate_path,
            as_attachment=True,
            download_name=download_filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        return jsonify({'error': f'Failed to download certificate: {str(e)}'}), 500

@certificate_bp.route('/verify/<certificate_id>', methods=['GET'])
def verify_certificate(certificate_id):
    """Verify a certificate by its ID (public endpoint)"""
    try:
        # Find assessment by certificate ID
        assessment = Assessment.query.filter_by(certificate_id=certificate_id).first()
        
        if not assessment:
            return jsonify({
                'valid': False,
                'error': 'Certificate not found'
            }), 404
        
        if not assessment.certificate_generated:
            return jsonify({
                'valid': False,
                'error': 'Certificate not generated'
            }), 404
        
        # Get user information
        user = User.query.get(assessment.user_id)
        
        # Return certificate verification information
        return jsonify({
            'valid': True,
            'certificate_id': certificate_id,
            'organization_name': assessment.organization_name,
            'ai_system_name': assessment.ai_system_name,
            'compliance_score': assessment.final_score,
            'risk_level': assessment.risk_level,
            'industry': assessment.industry,
            'issued_date': assessment.certificate_generated_at.strftime('%B %d, %Y') if assessment.certificate_generated_at else 'Unknown',
            'completion_date': assessment.completed_at.strftime('%B %d, %Y') if assessment.completed_at else 'Unknown',
            'status': 'Valid',
            'issuer': 'Qryti'
        })
        
    except Exception as e:
        return jsonify({
            'valid': False,
            'error': f'Verification failed: {str(e)}'
        }), 500

@certificate_bp.route('/list', methods=['GET'])
@jwt_required()
def list_certificates():
    """List all certificates for the current user"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get all assessments with certificates for the user
        assessments = Assessment.query.filter_by(
            user_id=current_user_id,
            certificate_generated=True
        ).order_by(Assessment.certificate_generated_at.desc()).all()
        
        certificates = []
        for assessment in assessments:
            certificates.append({
                'assessment_id': assessment.id,
                'certificate_id': assessment.certificate_id,
                'organization_name': assessment.organization_name,
                'ai_system_name': assessment.ai_system_name,
                'compliance_score': assessment.final_score,
                'risk_level': assessment.risk_level,
                'industry': assessment.industry,
                'issued_date': assessment.certificate_generated_at.strftime('%B %d, %Y') if assessment.certificate_generated_at else 'Unknown',
                'completion_date': assessment.completed_at.strftime('%B %d, %Y') if assessment.completed_at else 'Unknown',
                'download_url': f'/api/certificates/download/{assessment.id}'
            })
        
        return jsonify({
            'certificates': certificates,
            'total': len(certificates)
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to list certificates: {str(e)}'}), 500

@certificate_bp.route('/preview/<int:assessment_id>', methods=['GET'])
@jwt_required()
def preview_certificate(assessment_id):
    """Generate a preview of the certificate without saving it"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get the assessment
        assessment = Assessment.query.filter_by(
            id=assessment_id,
            user_id=current_user_id
        ).first()
        
        if not assessment:
            return jsonify({'error': 'Assessment not found'}), 404
        
        # Check if assessment meets requirements for certificate
        if assessment.status != 'completed':
            return jsonify({'error': 'Assessment must be completed to preview certificate'}), 400
        
        if not assessment.final_score or assessment.final_score < 70:
            return jsonify({
                'error': 'Assessment score must be 70% or higher to generate certificate',
                'current_score': assessment.final_score
            }), 400
        
        # Prepare certificate data
        certificate_data = {
            'organization_name': assessment.organization_name,
            'ai_system_name': assessment.ai_system_name,
            'ai_system_description': assessment.ai_system_description,
            'final_score': assessment.final_score,
            'risk_level': assessment.risk_level,
            'industry': assessment.industry,
            'completion_date': assessment.completed_at.strftime('%B %d, %Y') if assessment.completed_at else datetime.now().strftime('%B %d, %Y'),
            'certificate_id': f'PREVIEW-{assessment.id}-{datetime.now().strftime("%Y%m%d")}',
            'user_name': f'{user.first_name} {user.last_name}',
            'user_email': user.email,
            'assessment_id': assessment.id
        }
        
        # Generate certificate in a temporary file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            certificate_path = generate_compliance_certificate(certificate_data, os.path.dirname(temp_file.name))
            
            # Return the preview file
            return send_file(
                certificate_path,
                as_attachment=False,
                download_name=f"Certificate_Preview_{assessment.organization_name.replace(' ', '_')}.pdf",
                mimetype='application/pdf'
            )
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate certificate preview: {str(e)}'}), 500

