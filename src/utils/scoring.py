"""
ISO 42001 Compliance Scoring Algorithm
Implements the comprehensive scoring methodology for ISO 42001 compliance assessment
"""

import json
from typing import Dict, List, Any, Optional
from collections import defaultdict

# ISO 42001 Control Definitions with Assessment Stage Mapping
ISO42001_CONTROLS = {
    'A.2.2': {
        'name': 'AI Policy',
        'description': 'The organization shall document a policy for the development or use of AI systems.',
        'stage': 'policy_review',
        'domain': 'governance',
        'weight': 3,
        'questions': [
            'Is there a documented AI policy for development or use?',
            'Has management formally approved the policy?',
            'Does the policy define AI development and usage guidelines?'
        ],
        'evidence_required': ['AI Policy Document', 'Management Approval Records', 'Policy Review Logs']
    },
    'A.2.3': {
        'name': 'Alignment with other organizational policies',
        'description': 'The organization shall determine where other policies can be affected by or apply to AI objectives.',
        'stage': 'policy_review',
        'domain': 'governance',
        'weight': 2,
        'questions': [
            'Has the organization identified policies that may be impacted by AI objectives?',
            'Is there a process to assess policy interdependencies related to AI?',
            'Have affected policies been reviewed and updated to align with AI objectives?'
        ],
        'evidence_required': ['Policy Impact Assessment', 'Updated Policies', 'Review Records']
    },
    'A.2.4': {
        'name': 'Review of the AI policy',
        'description': 'The AI policy shall be reviewed at planned intervals to ensure continuing suitability.',
        'stage': 'policy_review',
        'domain': 'governance',
        'weight': 2,
        'questions': [
            'Is the AI policy reviewed at planned intervals?',
            'Are additional reviews conducted when significant changes occur?',
            'Is there a documented process for policy review and updates?'
        ],
        'evidence_required': ['Review Schedule', 'Review Records', 'Process Documentation']
    },
    'A.3.2': {
        'name': 'AI roles and responsibilities',
        'description': 'Roles and responsibilities for AI shall be defined and allocated according to organizational needs.',
        'stage': 'requirements_gathering',
        'domain': 'governance',
        'weight': 3,
        'questions': [
            'Have roles and responsibilities for AI been formally defined?',
            'Are AI-related responsibilities aligned with organizational needs?',
            'Has management approved and communicated AI roles and responsibilities?'
        ],
        'evidence_required': ['Role Documentation', 'Approval Records', 'Communication Logs']
    },
    'A.3.3': {
        'name': 'Reporting of concerns',
        'description': 'The organization shall define a process to report concerns about AI systems throughout their lifecycle.',
        'stage': 'policy_review',
        'domain': 'governance',
        'weight': 2,
        'questions': [
            'Is there a documented process for reporting AI-related concerns?',
            'Are reporting channels established and communicated?',
            'Are concerns tracked, reviewed, and resolved with documented actions?'
        ],
        'evidence_required': ['Reporting Procedure', 'Channel Documentation', 'Concern Records']
    },
    'A.4.2': {
        'name': 'Resource documentation',
        'description': 'The organization shall identify and document relevant resources required for AI activities.',
        'stage': 'requirements_gathering',
        'domain': 'resources',
        'weight': 2,
        'questions': [
            'Has the organization identified required resources for each AI lifecycle stage?',
            'Are human, technical, and financial resources explicitly defined?',
            'Has management formally approved the resource allocation for AI activities?'
        ],
        'evidence_required': ['Resource Requirements', 'Review Records', 'Approval Documentation']
    },
    'A.4.3': {
        'name': 'Data Resources',
        'description': 'The organization shall document information about data resources utilized for AI systems.',
        'stage': 'requirements_gathering',
        'domain': 'resources',
        'weight': 2,
        'questions': [
            'Has the organization documented the data resources used for AI systems?',
            'Does the documentation include data sources, types, and ownership?',
            'Are data resource records periodically reviewed and updated?'
        ],
        'evidence_required': ['Data Resource Inventory', 'Source Documentation', 'Review Records']
    },
    'A.5.2': {
        'name': 'AI system impact assessment process',
        'description': 'The organization shall establish a process to assess potential consequences of AI systems.',
        'stage': 'gap_assessment',
        'domain': 'impact_assessment',
        'weight': 5,
        'questions': [
            'Has the organization established a documented AI impact assessment process?',
            'Does the assessment cover all lifecycle stages of the AI system?',
            'Are ethical, legal, and social impacts considered in the assessment?'
        ],
        'evidence_required': ['Assessment Process', 'Assessment Records', 'Review Logs']
    },
    'A.5.4': {
        'name': 'Assessing AI system impact on individuals',
        'description': 'The organization shall assess and document potential impacts on individuals or groups.',
        'stage': 'gap_assessment',
        'domain': 'impact_assessment',
        'weight': 4,
        'questions': [
            'Has the organization conducted impact assessments on individuals or groups?',
            'Is the impact assessment documented and aligned with the AI system lifecycle?',
            'Are ethical, legal, and societal risks considered in the assessment?'
        ],
        'evidence_required': ['Impact Assessment Reports', 'Review Records', 'Risk Assessments']
    },
    'A.5.5': {
        'name': 'Assessing societal impacts of AI systems',
        'description': 'The organization shall assess and document potential societal impacts of AI systems.',
        'stage': 'gap_assessment',
        'domain': 'impact_assessment',
        'weight': 4,
        'questions': [
            'Has the organization conducted societal impact assessments?',
            'Are mitigation measures defined for identified negative societal impacts?',
            'Has management reviewed and approved the societal impact assessment?'
        ],
        'evidence_required': ['Societal Impact Reports', 'Mitigation Plans', 'Approval Records']
    },
    'A.6.1.2': {
        'name': 'Objectives for responsible development of AI system',
        'description': 'The organization shall identify objectives to guide responsible AI development.',
        'stage': 'requirements_gathering',
        'domain': 'development',
        'weight': 3,
        'questions': [
            'Has the organization identified objectives for responsible AI development?',
            'Are these objectives aligned with ethical, legal, and business requirements?',
            'Have measures been integrated into the AI development lifecycle?'
        ],
        'evidence_required': ['Development Objectives', 'Lifecycle Process', 'Review Records']
    },
    'A.6.2.4': {
        'name': 'AI system verification and validation',
        'description': 'The organization shall define verification and validation measures for AI systems.',
        'stage': 'implementation_status',
        'domain': 'development',
        'weight': 4,
        'questions': [
            'Has the organization defined V&V measures for AI systems?',
            'Are specific criteria for applying V&V measures clearly outlined?',
            'Has management approved and implemented the V&V framework?'
        ],
        'evidence_required': ['V&V Documentation', 'Criteria Definition', 'Approval Records']
    },
    'A.6.2.6': {
        'name': 'AI system operation and monitoring',
        'description': 'The organization shall define necessary elements for ongoing AI system operation.',
        'stage': 'implementation_status',
        'domain': 'operations',
        'weight': 4,
        'questions': [
            'Has the organization defined essential elements for AI system operation?',
            'Does the documentation specify system functionality and monitoring requirements?',
            'Are operational procedures regularly reviewed and updated?'
        ],
        'evidence_required': ['Operational Documentation', 'Monitoring Logs', 'Review Records']
    },
    'A.10.3': {
        'name': 'Suppliers',
        'description': 'The organization shall ensure supplier services align with responsible AI principles.',
        'stage': 'internal_audit',
        'domain': 'stakeholders',
        'weight': 3,
        'questions': [
            'Has the organization established a supplier AI compliance assessment process?',
            'Are AI-related supplier agreements reviewed for ethical AI use?',
            'Is there a mechanism to regularly monitor supplier compliance?'
        ],
        'evidence_required': ['Supplier Process', 'Assessment Records', 'Monitoring Reports']
    }
}

# Domain weights for overall score calculation
DOMAIN_WEIGHTS = {
    'impact_assessment': 0.25,
    'development': 0.20,
    'operations': 0.15,
    'governance': 0.15,
    'resources': 0.10,
    'stakeholders': 0.10,
    'documentation': 0.05
}

# Maturity level score mapping
MATURITY_SCORES = {
    0: 0,    # Not Implemented
    1: 20,   # Ad-hoc/Informal
    2: 40,   # Defined but Inconsistent
    3: 60,   # Managed and Implemented
    4: 80,   # Measured and Monitored
    5: 100   # Optimized and Continuously Improved
}

def get_iso42001_controls() -> Dict[str, Dict[str, Any]]:
    """Get the complete ISO 42001 control definitions"""
    return ISO42001_CONTROLS

def calculate_compliance_score(maturity_level: int, evidence_completeness: float, response_quality: float) -> float:
    """
    Calculate base compliance score for a single control
    
    Args:
        maturity_level: Maturity level (0-5)
        evidence_completeness: Evidence completeness factor (0.0-1.0)
        response_quality: Response quality factor (0.0-1.0)
    
    Returns:
        Calculated score (0.0-100.0)
    """
    if maturity_level not in MATURITY_SCORES:
        return 0.0
    
    base_score = MATURITY_SCORES[maturity_level]
    
    # Apply evidence completeness adjustment (±10%)
    evidence_adjustment = (evidence_completeness - 0.5) * 0.2
    base_score *= (1 + evidence_adjustment)
    
    # Apply response quality adjustment (±5%)
    quality_adjustment = (response_quality - 0.5) * 0.1
    base_score *= (1 + quality_adjustment)
    
    return max(0.0, min(100.0, base_score))

def calculate_domain_score(responses: List[Any], domain: str) -> Dict[str, Any]:
    """
    Calculate aggregated score for a specific domain
    
    Args:
        responses: List of AssessmentResponse objects
        domain: Domain name
    
    Returns:
        Dictionary with domain score and statistics
    """
    domain_responses = [r for r in responses if r.domain == domain and r.calculated_score is not None]
    
    if not domain_responses:
        return {
            'score': 0.0,
            'response_count': 0,
            'average_maturity': 0.0,
            'completion_rate': 0.0
        }
    
    # Get domain controls
    domain_controls = {k: v for k, v in ISO42001_CONTROLS.items() if v['domain'] == domain}
    
    # Calculate weighted score
    total_weighted_score = 0.0
    total_weight = 0.0
    
    for response in domain_responses:
        control_info = domain_controls.get(response.control_id, {})
        weight = control_info.get('weight', 1)
        
        total_weighted_score += response.calculated_score * weight
        total_weight += weight
    
    domain_score = total_weighted_score / total_weight if total_weight > 0 else 0.0
    
    # Calculate statistics
    maturity_levels = [r.maturity_level for r in domain_responses if r.maturity_level is not None]
    average_maturity = sum(maturity_levels) / len(maturity_levels) if maturity_levels else 0.0
    completion_rate = len(domain_responses) / len(domain_controls) if domain_controls else 0.0
    
    return {
        'score': round(domain_score, 2),
        'response_count': len(domain_responses),
        'average_maturity': round(average_maturity, 2),
        'completion_rate': round(completion_rate * 100, 1)
    }

def apply_risk_adjustments(base_score: float, risk_level: str) -> float:
    """
    Apply risk-based adjustments to compliance scores
    
    Args:
        base_score: Base compliance score
        risk_level: Risk level (low, medium, high)
    
    Returns:
        Risk-adjusted score
    """
    risk_adjustments = {
        'low': 1.0,      # No adjustment
        'medium': 0.95,  # 5% penalty
        'high': 0.90     # 10% penalty
    }
    
    adjustment_factor = risk_adjustments.get(risk_level.lower(), 1.0)
    return max(0.0, min(100.0, base_score * adjustment_factor))

def calculate_confidence_interval(score: float, assessment_completeness: float, evidence_quality: float) -> Dict[str, float]:
    """
    Calculate confidence interval for compliance score
    
    Args:
        score: Calculated compliance score
        assessment_completeness: Assessment completion rate (0.0-1.0)
        evidence_quality: Average evidence quality (0.0-1.0)
    
    Returns:
        Dictionary with confidence interval data
    """
    # Base confidence starts at 95% for complete assessments
    confidence = 0.95
    
    # Reduce confidence based on assessment completeness
    confidence *= assessment_completeness
    
    # Reduce confidence based on evidence quality
    confidence *= evidence_quality
    
    # Calculate margin of error (wider intervals for lower confidence)
    margin_of_error = (1 - confidence) * 20  # Max 20 point margin
    
    return {
        'score': round(score, 2),
        'confidence': round(confidence, 3),
        'lower_bound': round(max(0, score - margin_of_error), 2),
        'upper_bound': round(min(100, score + margin_of_error), 2),
        'margin_of_error': round(margin_of_error, 2)
    }

def calculate_maturity_distribution(responses: List[Any]) -> Dict[str, Any]:
    """
    Calculate maturity level distribution across all responses
    
    Args:
        responses: List of AssessmentResponse objects
    
    Returns:
        Dictionary with maturity distribution statistics
    """
    maturity_counts = defaultdict(int)
    total_responses = 0
    
    for response in responses:
        if response.maturity_level is not None:
            maturity_counts[response.maturity_level] += 1
            total_responses += 1
    
    if total_responses == 0:
        return {
            'distribution': {str(i): 0 for i in range(6)},
            'average_maturity': 0.0,
            'total_responses': 0
        }
    
    # Calculate percentages
    distribution = {}
    weighted_sum = 0
    
    for level in range(6):
        count = maturity_counts[level]
        percentage = (count / total_responses) * 100
        distribution[str(level)] = round(percentage, 1)
        weighted_sum += level * count
    
    average_maturity = weighted_sum / total_responses
    
    return {
        'distribution': distribution,
        'average_maturity': round(average_maturity, 2),
        'total_responses': total_responses
    }

def calculate_assessment_scores(responses: List[Any], risk_level: str = 'medium') -> Dict[str, Any]:
    """
    Calculate comprehensive compliance scores for an assessment
    
    Args:
        responses: List of AssessmentResponse objects
        risk_level: Risk level for risk-based adjustments
    
    Returns:
        Dictionary with comprehensive scoring results
    """
    # Calculate domain scores
    domain_scores = {}
    for domain in DOMAIN_WEIGHTS.keys():
        domain_scores[domain] = calculate_domain_score(responses, domain)
    
    # Calculate overall score using domain weights
    total_weighted_score = 0.0
    total_weight = 0.0
    
    for domain, weight in DOMAIN_WEIGHTS.items():
        domain_data = domain_scores.get(domain, {'score': 0.0})
        if domain_data['score'] > 0:  # Only include domains with responses
            total_weighted_score += domain_data['score'] * weight
            total_weight += weight
    
    overall_score = total_weighted_score / total_weight if total_weight > 0 else 0.0
    
    # Apply risk adjustments
    risk_adjusted_score = apply_risk_adjustments(overall_score, risk_level)
    
    # Calculate control-level scores
    control_scores = {}
    for response in responses:
        if response.calculated_score is not None:
            control_scores[response.control_id] = {
                'score': response.calculated_score,
                'maturity_level': response.maturity_level,
                'evidence_completeness': response.evidence_completeness,
                'response_quality': response.response_quality
            }
    
    # Calculate assessment completeness and evidence quality
    total_controls = len(ISO42001_CONTROLS)
    completed_responses = len([r for r in responses if r.maturity_level is not None])
    assessment_completeness = completed_responses / total_controls if total_controls > 0 else 0.0
    
    evidence_qualities = [r.evidence_completeness for r in responses if r.evidence_completeness is not None]
    average_evidence_quality = sum(evidence_qualities) / len(evidence_qualities) if evidence_qualities else 0.5
    
    # Calculate confidence interval
    confidence_interval = calculate_confidence_interval(
        risk_adjusted_score,
        assessment_completeness,
        average_evidence_quality
    )
    
    # Calculate maturity distribution
    maturity_distribution = calculate_maturity_distribution(responses)
    
    return {
        'overall_score': round(risk_adjusted_score, 2),
        'base_score': round(overall_score, 2),
        'risk_adjustment': risk_level,
        'domain_scores': {domain: data['score'] for domain, data in domain_scores.items()},
        'domain_details': domain_scores,
        'control_scores': control_scores,
        'maturity_distribution': maturity_distribution,
        'confidence_interval': confidence_interval,
        'assessment_completeness': round(assessment_completeness * 100, 1),
        'average_evidence_quality': round(average_evidence_quality, 3),
        'total_responses': len(responses),
        'completed_responses': completed_responses,
        'calculation_metadata': {
            'domain_weights': DOMAIN_WEIGHTS,
            'maturity_scores': MATURITY_SCORES,
            'total_controls': total_controls
        }
    }

