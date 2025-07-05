"""
Assessment Response Validation Utility
Validates user responses to ISO 42001 assessment questions
"""

from typing import Dict, List, Any, Optional
import re

def validate_assessment_response(response, control_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate an assessment response for completeness and quality
    
    Args:
        response: AssessmentResponse object
        control_info: Control definition from ISO42001_CONTROLS
    
    Returns:
        Dictionary with validation results
    """
    validation_result = {
        'is_valid': True,
        'errors': [],
        'warnings': [],
        'evidence_completeness': 0.5,
        'response_quality': 0.5,
        'completeness_score': 0.0
    }
    
    responses_data = response.get_responses()
    
    # Validate maturity level
    if response.maturity_level is None:
        validation_result['errors'].append("Maturity level is required")
        validation_result['is_valid'] = False
    elif not (0 <= response.maturity_level <= 5):
        validation_result['errors'].append("Maturity level must be between 0 and 5")
        validation_result['is_valid'] = False
    
    # Validate question responses
    questions = responses_data.get('questions', [])
    required_questions = control_info.get('questions', [])
    
    if not questions:
        validation_result['errors'].append("No responses provided to assessment questions")
        validation_result['is_valid'] = False
    else:
        # Check response completeness
        answered_questions = len([q for q in questions if q.get('answer')])
        total_questions = len(required_questions)
        
        if total_questions > 0:
            completeness_ratio = answered_questions / total_questions
            validation_result['completeness_score'] = completeness_ratio
            
            if completeness_ratio < 0.5:
                validation_result['warnings'].append(
                    f"Only {answered_questions} of {total_questions} questions answered"
                )
        
        # Validate individual question responses
        for i, question_response in enumerate(questions):
            question_validation = validate_question_response(question_response, i)
            validation_result['errors'].extend(question_validation['errors'])
            validation_result['warnings'].extend(question_validation['warnings'])
    
    # Calculate evidence completeness
    evidence_completeness = calculate_evidence_completeness(response, control_info)
    validation_result['evidence_completeness'] = evidence_completeness
    
    # Calculate response quality
    response_quality = calculate_response_quality(responses_data, control_info)
    validation_result['response_quality'] = response_quality
    
    # Overall validation
    if validation_result['errors']:
        validation_result['is_valid'] = False
    
    return validation_result

def validate_question_response(question_response: Dict[str, Any], question_index: int) -> Dict[str, Any]:
    """
    Validate a single question response
    
    Args:
        question_response: Individual question response data
        question_index: Index of the question
    
    Returns:
        Dictionary with validation results for the question
    """
    result = {
        'errors': [],
        'warnings': []
    }
    
    answer = question_response.get('answer', '')
    question_type = question_response.get('type', 'text')
    
    if not answer:
        result['warnings'].append(f"Question {question_index + 1} has no answer")
        return result
    
    # Validate based on question type
    if question_type == 'text':
        if len(str(answer).strip()) < 10:
            result['warnings'].append(
                f"Question {question_index + 1} answer is very short (less than 10 characters)"
            )
    
    elif question_type == 'multiple_choice':
        valid_options = question_response.get('options', [])
        if answer not in valid_options:
            result['errors'].append(
                f"Question {question_index + 1} has invalid multiple choice answer"
            )
    
    elif question_type == 'rating':
        try:
            rating = float(answer)
            min_rating = question_response.get('min_rating', 1)
            max_rating = question_response.get('max_rating', 5)
            
            if not (min_rating <= rating <= max_rating):
                result['errors'].append(
                    f"Question {question_index + 1} rating must be between {min_rating} and {max_rating}"
                )
        except (ValueError, TypeError):
            result['errors'].append(
                f"Question {question_index + 1} rating must be a number"
            )
    
    elif question_type == 'boolean':
        if answer not in [True, False, 'true', 'false', 'yes', 'no']:
            result['errors'].append(
                f"Question {question_index + 1} must have a yes/no or true/false answer"
            )
    
    return result

def calculate_evidence_completeness(response, control_info: Dict[str, Any]) -> float:
    """
    Calculate evidence completeness score
    
    Args:
        response: AssessmentResponse object
        control_info: Control definition
    
    Returns:
        Evidence completeness score (0.0-1.0)
    """
    evidence_files = response.get_evidence_files()
    required_evidence = control_info.get('evidence_required', [])
    
    if not required_evidence:
        return 1.0  # No evidence required
    
    if not evidence_files:
        return 0.0  # No evidence provided
    
    # Basic completeness based on number of files vs required evidence types
    evidence_ratio = min(len(evidence_files) / len(required_evidence), 1.0)
    
    # Bonus for having more evidence than minimum required
    if len(evidence_files) > len(required_evidence):
        evidence_ratio = min(evidence_ratio + 0.1, 1.0)
    
    return evidence_ratio

def calculate_response_quality(responses_data: Dict[str, Any], control_info: Dict[str, Any]) -> float:
    """
    Calculate response quality score based on completeness and detail
    
    Args:
        responses_data: Response data dictionary
        control_info: Control definition
    
    Returns:
        Response quality score (0.0-1.0)
    """
    quality_score = 0.5  # Base score
    
    questions = responses_data.get('questions', [])
    if not questions:
        return 0.0
    
    # Analyze response quality factors
    total_length = 0
    answered_questions = 0
    detailed_responses = 0
    
    for question in questions:
        answer = question.get('answer', '')
        if answer:
            answered_questions += 1
            answer_length = len(str(answer).strip())
            total_length += answer_length
            
            # Consider responses with more than 50 characters as detailed
            if answer_length > 50:
                detailed_responses += 1
    
    if answered_questions == 0:
        return 0.0
    
    # Calculate quality factors
    completeness_factor = answered_questions / len(questions)
    detail_factor = detailed_responses / answered_questions
    average_length = total_length / answered_questions
    
    # Length quality (diminishing returns after 200 characters)
    length_quality = min(average_length / 200, 1.0)
    
    # Combine factors
    quality_score = (
        completeness_factor * 0.4 +
        detail_factor * 0.3 +
        length_quality * 0.3
    )
    
    # Check for comments
    if responses_data.get('comments'):
        comment_length = len(responses_data['comments'].strip())
        if comment_length > 20:
            quality_score = min(quality_score + 0.1, 1.0)
    
    return min(max(quality_score, 0.0), 1.0)

def validate_file_upload(file_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate uploaded evidence file
    
    Args:
        file_data: File upload data
    
    Returns:
        Dictionary with validation results
    """
    result = {
        'is_valid': True,
        'errors': [],
        'warnings': []
    }
    
    # Allowed file types
    allowed_extensions = {
        '.pdf', '.doc', '.docx', '.txt', '.rtf',  # Documents
        '.jpg', '.jpeg', '.png', '.gif', '.bmp',  # Images
        '.xls', '.xlsx', '.csv',                  # Spreadsheets
        '.ppt', '.pptx',                          # Presentations
        '.zip', '.rar'                            # Archives
    }
    
    # Check file extension
    filename = file_data.get('filename', '')
    if not filename:
        result['errors'].append("Filename is required")
        result['is_valid'] = False
        return result
    
    file_extension = '.' + filename.split('.')[-1].lower() if '.' in filename else ''
    
    if file_extension not in allowed_extensions:
        result['errors'].append(
            f"File type {file_extension} is not allowed. "
            f"Allowed types: {', '.join(sorted(allowed_extensions))}"
        )
        result['is_valid'] = False
    
    # Check file size (16MB limit)
    file_size = file_data.get('size', 0)
    max_size = 16 * 1024 * 1024  # 16MB
    
    if file_size > max_size:
        result['errors'].append(
            f"File size ({file_size / 1024 / 1024:.1f}MB) exceeds maximum allowed size (16MB)"
        )
        result['is_valid'] = False
    
    if file_size == 0:
        result['errors'].append("File appears to be empty")
        result['is_valid'] = False
    
    # Check filename for security
    if not is_safe_filename(filename):
        result['errors'].append("Filename contains invalid characters")
        result['is_valid'] = False
    
    return result

def is_safe_filename(filename: str) -> bool:
    """
    Check if filename is safe (no path traversal, etc.)
    
    Args:
        filename: Filename to check
    
    Returns:
        True if filename is safe
    """
    # Check for path traversal attempts
    if '..' in filename or '/' in filename or '\\' in filename:
        return False
    
    # Check for valid characters (alphanumeric, spaces, dots, hyphens, underscores)
    if not re.match(r'^[a-zA-Z0-9\s\.\-_]+$', filename):
        return False
    
    # Check length
    if len(filename) > 255:
        return False
    
    return True

def validate_assessment_data(assessment_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate assessment creation/update data
    
    Args:
        assessment_data: Assessment data dictionary
    
    Returns:
        Dictionary with validation results
    """
    result = {
        'is_valid': True,
        'errors': [],
        'warnings': []
    }
    
    # Required fields
    required_fields = {
        'assessmentName': 'Assessment name',
        'organizationName': 'Organization name',
        'aiSystemDescription': 'AI system description',
        'industry': 'Industry',
        'riskLevel': 'Risk level'
    }
    
    for field, display_name in required_fields.items():
        if not assessment_data.get(field):
            result['errors'].append(f"{display_name} is required")
            result['is_valid'] = False
        elif len(str(assessment_data[field]).strip()) < 2:
            result['errors'].append(f"{display_name} must be at least 2 characters long")
            result['is_valid'] = False
    
    # Validate risk level
    risk_level = assessment_data.get('riskLevel', '').lower()
    if risk_level not in ['low', 'medium', 'high']:
        result['errors'].append("Risk level must be 'low', 'medium', or 'high'")
        result['is_valid'] = False
    
    # Validate AI system description length
    ai_description = assessment_data.get('aiSystemDescription', '')
    if len(ai_description.strip()) < 50:
        result['warnings'].append(
            "AI system description is quite short. Consider providing more detail for better assessment."
        )
    
    # Validate organization name
    org_name = assessment_data.get('organizationName', '')
    if len(org_name.strip()) < 2:
        result['errors'].append("Organization name must be at least 2 characters long")
        result['is_valid'] = False
    
    return result

