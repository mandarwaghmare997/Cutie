from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import json

from src.models.user import User, db
from src.models.assessment import Assessment, AssessmentResponse, AssessmentFile
from src.utils.scoring import calculate_compliance_score, get_iso42001_controls
from src.utils.validation import validate_assessment_response

assessment_bp = Blueprint('assessment', __name__)

@assessment_bp.route('', methods=['POST'])
@jwt_required()
def create_assessment():
    """Create a new compliance assessment"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['assessmentName', 'organizationName', 'aiSystemDescription', 'industry', 'riskLevel']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                'error': 'validation_error',
                'message': 'Missing required fields',
                'details': [f'{field} is required' for field in missing_fields]
            }), 400
        
        # Validate risk level
        if data['riskLevel'] not in ['low', 'medium', 'high']:
            return jsonify({
                'error': 'validation_error',
                'message': 'Risk level must be low, medium, or high'
            }), 400
        
        # Create assessment
        assessment = Assessment(
            user_id=current_user_id,
            assessment_name=data['assessmentName'],
            organization_name=data['organizationName'],
            ai_system_description=data['aiSystemDescription'],
            industry=data['industry'],
            risk_level=data['riskLevel'],
            regulatory_requirements=data.get('regulatoryRequirements', [])
        )
        
        db.session.add(assessment)
        db.session.commit()
        
        return jsonify(assessment.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Create assessment error: {str(e)}")
        return jsonify({
            'error': 'internal_error',
            'message': 'An error occurred while creating the assessment'
        }), 500

@assessment_bp.route('', methods=['GET'])
@jwt_required()
def get_assessments():
    """Get all assessments for the current user"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get query parameters
        status = request.args.get('status')
        limit = request.args.get('limit', 10, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = Assessment.query.filter_by(user_id=current_user_id)
        
        if status:
            query = query.filter_by(status=status)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        assessments = query.order_by(Assessment.created_at.desc()).offset(offset).limit(limit).all()
        
        return jsonify({
            'assessments': [assessment.to_dict() for assessment in assessments],
            'total': total,
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get assessments error: {str(e)}")
        return jsonify({
            'error': 'internal_error',
            'message': 'An error occurred while fetching assessments'
        }), 500

@assessment_bp.route('/<assessment_id>', methods=['GET'])
@jwt_required()
def get_assessment(assessment_id):
    """Get a specific assessment"""
    try:
        current_user_id = get_jwt_identity()
        
        assessment = Assessment.query.filter_by(
            id=assessment_id,
            user_id=current_user_id
        ).first()
        
        if not assessment:
            return jsonify({
                'error': 'assessment_not_found',
                'message': 'Assessment not found or access denied'
            }), 404
        
        include_responses = request.args.get('include_responses', 'false').lower() == 'true'
        
        return jsonify(assessment.to_dict(include_responses=include_responses)), 200
        
    except Exception as e:
        current_app.logger.error(f"Get assessment error: {str(e)}")
        return jsonify({
            'error': 'internal_error',
            'message': 'An error occurred while fetching the assessment'
        }), 500

@assessment_bp.route('/<assessment_id>', methods=['PUT'])
@jwt_required()
def update_assessment(assessment_id):
    """Update assessment metadata"""
    try:
        current_user_id = get_jwt_identity()
        
        assessment = Assessment.query.filter_by(
            id=assessment_id,
            user_id=current_user_id
        ).first()
        
        if not assessment:
            return jsonify({
                'error': 'assessment_not_found',
                'message': 'Assessment not found or access denied'
            }), 404
        
        data = request.get_json()
        
        # Update allowed fields
        updatable_fields = ['assessment_name', 'organization_name', 'ai_system_description', 
                           'industry', 'risk_level']
        
        for field in updatable_fields:
            if field in data:
                setattr(assessment, field, data[field])
        
        if 'regulatoryRequirements' in data:
            assessment.set_regulatory_requirements(data['regulatoryRequirements'])
        
        assessment.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(assessment.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update assessment error: {str(e)}")
        return jsonify({
            'error': 'internal_error',
            'message': 'An error occurred while updating the assessment'
        }), 500

@assessment_bp.route('/<assessment_id>/responses', methods=['PUT'])
@jwt_required()
def submit_response(assessment_id):
    """Submit or update assessment response"""
    try:
        current_user_id = get_jwt_identity()
        
        assessment = Assessment.query.filter_by(
            id=assessment_id,
            user_id=current_user_id
        ).first()
        
        if not assessment:
            return jsonify({
                'error': 'assessment_not_found',
                'message': 'Assessment not found or access denied'
            }), 404
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['stage', 'controlId', 'responses']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                'error': 'validation_error',
                'message': 'Missing required fields',
                'details': [f'{field} is required' for field in missing_fields]
            }), 400
        
        control_id = data['controlId']
        stage = data['stage']
        
        # Get control information
        controls = get_iso42001_controls()
        control_info = controls.get(control_id)
        
        if not control_info:
            return jsonify({
                'error': 'invalid_control',
                'message': f'Invalid control ID: {control_id}'
            }), 400
        
        # Find or create response
        response = AssessmentResponse.query.filter_by(
            assessment_id=assessment_id,
            control_id=control_id
        ).first()
        
        if not response:
            response = AssessmentResponse(
                assessment_id=assessment_id,
                control_id=control_id,
                stage=stage,
                domain=control_info['domain']
            )
            db.session.add(response)
        
        # Update response data
        response.set_responses(data['responses'])
        response.maturity_level = data['responses'].get('maturityLevel')
        response.comments = data.get('comments')
        
        if 'evidenceFiles' in data:
            response.set_evidence_files(data['evidenceFiles'])
        
        # Validate response
        validation_result = validate_assessment_response(response, control_info)
        response.evidence_completeness = validation_result.get('evidence_completeness', 0.5)
        response.response_quality = validation_result.get('response_quality', 0.5)
        
        # Calculate score for this control
        if response.maturity_level is not None:
            response.calculated_score = calculate_compliance_score(
                response.maturity_level,
                response.evidence_completeness,
                response.response_quality
            )
        
        response.updated_at = datetime.utcnow()
        
        # Update assessment progress
        stage_responses = AssessmentResponse.query.filter_by(
            assessment_id=assessment_id,
            stage=stage
        ).all()
        
        # Calculate stage progress based on completed responses
        stage_controls = [c for c in controls.values() if c['stage'] == stage]
        completed_responses = len([r for r in stage_responses if r.maturity_level is not None])
        stage_progress = (completed_responses / len(stage_controls)) * 100 if stage_controls else 0
        
        assessment.update_stage_progress(stage, stage_progress)
        
        db.session.commit()
        
        return jsonify({
            'assessmentId': assessment_id,
            'controlId': control_id,
            'stage': stage,
            'progress': assessment.get_progress(),
            'validationResults': validation_result,
            'response': response.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Submit response error: {str(e)}")
        return jsonify({
            'error': 'internal_error',
            'message': 'An error occurred while submitting the response'
        }), 500

@assessment_bp.route('/<assessment_id>/responses', methods=['GET'])
@jwt_required()
def get_responses(assessment_id):
    """Get all responses for an assessment"""
    try:
        current_user_id = get_jwt_identity()
        
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
        stage = request.args.get('stage')
        control_id = request.args.get('control_id')
        
        # Build query
        query = AssessmentResponse.query.filter_by(assessment_id=assessment_id)
        
        if stage:
            query = query.filter_by(stage=stage)
        
        if control_id:
            query = query.filter_by(control_id=control_id)
        
        responses = query.all()
        
        return jsonify({
            'responses': [response.to_dict() for response in responses],
            'total': len(responses)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get responses error: {str(e)}")
        return jsonify({
            'error': 'internal_error',
            'message': 'An error occurred while fetching responses'
        }), 500

@assessment_bp.route('/<assessment_id>/calculate-score', methods=['POST'])
@jwt_required()
def calculate_score(assessment_id):
    """Calculate compliance scores for an assessment"""
    try:
        current_user_id = get_jwt_identity()
        
        assessment = Assessment.query.filter_by(
            id=assessment_id,
            user_id=current_user_id
        ).first()
        
        if not assessment:
            return jsonify({
                'error': 'assessment_not_found',
                'message': 'Assessment not found or access denied'
            }), 404
        
        # Get all responses for the assessment
        responses = AssessmentResponse.query.filter_by(assessment_id=assessment_id).all()
        
        if not responses:
            return jsonify({
                'error': 'no_responses',
                'message': 'No responses found for this assessment'
            }), 400
        
        # Calculate scores using the scoring algorithm
        from src.utils.scoring import calculate_assessment_scores
        
        scores = calculate_assessment_scores(responses, assessment.risk_level)
        
        # Save scores to assessment
        assessment.set_scores(scores)
        assessment.updated_at = datetime.utcnow()
        
        # Check if assessment is complete
        controls = get_iso42001_controls()
        total_controls = len(controls)
        completed_responses = len([r for r in responses if r.maturity_level is not None])
        
        if completed_responses >= total_controls * 0.8:  # 80% completion threshold
            assessment.complete_assessment()
        
        db.session.commit()
        
        return jsonify({
            'assessmentId': assessment_id,
            'overallScore': scores['overall_score'],
            'domainScores': scores['domain_scores'],
            'controlScores': scores['control_scores'],
            'maturityDistribution': scores['maturity_distribution'],
            'confidenceInterval': scores['confidence_interval'],
            'calculatedAt': datetime.utcnow().isoformat(),
            'completionPercentage': (completed_responses / total_controls) * 100
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Calculate score error: {str(e)}")
        return jsonify({
            'error': 'internal_error',
            'message': 'An error occurred while calculating scores'
        }), 500

@assessment_bp.route('/<assessment_id>/advance-stage', methods=['POST'])
@jwt_required()
def advance_stage(assessment_id):
    """Advance assessment to the next stage"""
    try:
        current_user_id = get_jwt_identity()
        
        assessment = Assessment.query.filter_by(
            id=assessment_id,
            user_id=current_user_id
        ).first()
        
        if not assessment:
            return jsonify({
                'error': 'assessment_not_found',
                'message': 'Assessment not found or access denied'
            }), 404
        
        # Check if current stage is sufficiently complete
        current_stage = assessment.current_stage
        progress = assessment.get_progress()
        current_stage_progress = progress['stages'].get(current_stage, 0)
        
        if current_stage_progress < 80:  # Require 80% completion to advance
            return jsonify({
                'error': 'stage_incomplete',
                'message': f'Current stage must be at least 80% complete to advance. Current: {current_stage_progress}%'
            }), 400
        
        # Advance to next stage
        if assessment.advance_stage():
            assessment.updated_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'assessmentId': assessment_id,
                'previousStage': current_stage,
                'currentStage': assessment.current_stage,
                'progress': assessment.get_progress()
            }), 200
        else:
            return jsonify({
                'error': 'final_stage',
                'message': 'Assessment is already in the final stage'
            }), 400
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Advance stage error: {str(e)}")
        return jsonify({
            'error': 'internal_error',
            'message': 'An error occurred while advancing the stage'
        }), 500

@assessment_bp.route('/<assessment_id>/report', methods=['GET'])
@jwt_required()
def generate_report(assessment_id):
    """Generate compliance report"""
    try:
        current_user_id = get_jwt_identity()
        
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
        report_format = request.args.get('format', 'json')
        report_type = request.args.get('type', 'executive')
        
        # Get assessment data
        responses = AssessmentResponse.query.filter_by(assessment_id=assessment_id).all()
        user = User.query.get(current_user_id)
        
        # Generate report data
        from src.utils.reporting import generate_compliance_report
        
        report_data = generate_compliance_report(
            assessment=assessment,
            responses=responses,
            user=user,
            report_type=report_type
        )
        
        if report_format == 'json':
            return jsonify(report_data), 200
        elif report_format == 'pdf':
            # TODO: Implement PDF generation
            return jsonify({
                'error': 'not_implemented',
                'message': 'PDF generation not yet implemented'
            }), 501
        else:
            return jsonify({
                'error': 'invalid_format',
                'message': 'Supported formats: json, pdf'
            }), 400
        
    except Exception as e:
        current_app.logger.error(f"Generate report error: {str(e)}")
        return jsonify({
            'error': 'internal_error',
            'message': 'An error occurred while generating the report'
        }), 500

@assessment_bp.route('/controls', methods=['GET'])
def get_controls():
    """Get ISO 42001 control definitions"""
    try:
        controls = get_iso42001_controls()
        
        # Filter by stage if specified
        stage = request.args.get('stage')
        if stage:
            controls = {k: v for k, v in controls.items() if v['stage'] == stage}
        
        return jsonify({
            'controls': controls,
            'total': len(controls)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get controls error: {str(e)}")
        return jsonify({
            'error': 'internal_error',
            'message': 'An error occurred while fetching controls'
        }), 500

