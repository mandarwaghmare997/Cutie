"""
Compliance Reporting Utility
Generates comprehensive compliance reports for ISO 42001 assessments
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
import json

def generate_compliance_report(assessment, responses: List[Any], user, report_type: str = 'executive') -> Dict[str, Any]:
    """
    Generate a comprehensive compliance report
    
    Args:
        assessment: Assessment object
        responses: List of AssessmentResponse objects
        user: User object
        report_type: Type of report ('executive', 'detailed', 'technical')
    
    Returns:
        Dictionary containing the complete report
    """
    
    # Get assessment scores
    scores = assessment.get_scores() or {}
    progress = assessment.get_progress()
    
    # Base report structure
    report = {
        'report_metadata': {
            'report_type': report_type,
            'generated_at': datetime.utcnow().isoformat(),
            'assessment_id': assessment.id,
            'organization': assessment.organization_name,
            'ai_system': assessment.ai_system_description,
            'assessment_period': {
                'start_date': assessment.created_at.isoformat(),
                'end_date': assessment.completed_at.isoformat() if assessment.completed_at else None,
                'duration_days': (assessment.completed_at - assessment.created_at).days if assessment.completed_at else None
            }
        },
        'executive_summary': generate_executive_summary(assessment, scores, responses),
        'compliance_overview': generate_compliance_overview(scores, progress),
        'domain_analysis': generate_domain_analysis(responses, scores),
        'recommendations': generate_recommendations(assessment, responses, scores),
        'appendices': {
            'methodology': get_methodology_description(),
            'control_definitions': get_control_definitions_summary()
        }
    }
    
    # Add detailed sections based on report type
    if report_type in ['detailed', 'technical']:
        report['detailed_findings'] = generate_detailed_findings(responses)
        report['evidence_summary'] = generate_evidence_summary(responses)
        
    if report_type == 'technical':
        report['technical_details'] = generate_technical_details(assessment, responses, scores)
        report['raw_data'] = generate_raw_data_section(assessment, responses)
    
    return report

def generate_executive_summary(assessment, scores: Dict[str, Any], responses: List[Any]) -> Dict[str, Any]:
    """Generate executive summary section"""
    
    overall_score = scores.get('overall_score', 0)
    confidence_interval = scores.get('confidence_interval', {})
    maturity_distribution = scores.get('maturity_distribution', {})
    
    # Determine compliance level
    if overall_score >= 90:
        compliance_level = 'Excellent'
        compliance_description = 'Organization demonstrates exceptional AI governance and compliance practices.'
    elif overall_score >= 70:
        compliance_level = 'Good'
        compliance_description = 'Organization has solid AI governance foundations with room for improvement.'
    elif overall_score >= 50:
        compliance_level = 'Fair'
        compliance_description = 'Organization has basic AI governance practices but requires significant improvements.'
    else:
        compliance_level = 'Poor'
        compliance_description = 'Organization lacks adequate AI governance and requires immediate attention.'
    
    # Key findings
    key_findings = []
    
    # Analyze domain scores
    domain_scores = scores.get('domain_scores', {})
    strongest_domain = max(domain_scores.items(), key=lambda x: x[1]) if domain_scores else ('N/A', 0)
    weakest_domain = min(domain_scores.items(), key=lambda x: x[1]) if domain_scores else ('N/A', 0)
    
    if strongest_domain[1] > 0:
        key_findings.append(f"Strongest performance in {strongest_domain[0]} domain ({strongest_domain[1]:.1f}%)")
    
    if weakest_domain[1] < overall_score:
        key_findings.append(f"Improvement needed in {weakest_domain[0]} domain ({weakest_domain[1]:.1f}%)")
    
    # Analyze maturity levels
    avg_maturity = maturity_distribution.get('average_maturity', 0)
    if avg_maturity >= 4:
        key_findings.append("High maturity levels across most controls")
    elif avg_maturity < 2:
        key_findings.append("Low maturity levels indicate need for foundational improvements")
    
    return {
        'overall_score': overall_score,
        'compliance_level': compliance_level,
        'compliance_description': compliance_description,
        'confidence_interval': confidence_interval,
        'key_findings': key_findings,
        'assessment_completeness': scores.get('assessment_completeness', 0),
        'total_responses': len(responses),
        'risk_level': assessment.risk_level,
        'industry': assessment.industry
    }

def generate_compliance_overview(scores: Dict[str, Any], progress: Dict[str, Any]) -> Dict[str, Any]:
    """Generate compliance overview section"""
    
    domain_scores = scores.get('domain_scores', {})
    maturity_distribution = scores.get('maturity_distribution', {})
    
    # Calculate compliance gaps
    compliance_gaps = []
    for domain, score in domain_scores.items():
        if score < 70:  # Below good threshold
            gap_percentage = 70 - score
            compliance_gaps.append({
                'domain': domain,
                'current_score': score,
                'target_score': 70,
                'gap_percentage': gap_percentage,
                'priority': 'High' if gap_percentage > 30 else 'Medium'
            })
    
    # Stage completion analysis
    stage_progress = progress.get('stages', {})
    completed_stages = [stage for stage, prog in stage_progress.items() if prog >= 100]
    in_progress_stages = [stage for stage, prog in stage_progress.items() if 0 < prog < 100]
    
    return {
        'domain_scores': domain_scores,
        'maturity_distribution': maturity_distribution,
        'compliance_gaps': compliance_gaps,
        'stage_completion': {
            'completed': completed_stages,
            'in_progress': in_progress_stages,
            'overall_progress': progress.get('overall', 0)
        },
        'risk_assessment': {
            'overall_risk': 'Low' if scores.get('overall_score', 0) >= 80 else 'Medium' if scores.get('overall_score', 0) >= 60 else 'High',
            'confidence_level': scores.get('confidence_interval', {}).get('confidence', 0)
        }
    }

def generate_domain_analysis(responses: List[Any], scores: Dict[str, Any]) -> Dict[str, Any]:
    """Generate detailed domain analysis"""
    
    from src.utils.scoring import get_iso42001_controls, DOMAIN_WEIGHTS
    
    controls = get_iso42001_controls()
    domain_details = scores.get('domain_details', {})
    
    domain_analysis = {}
    
    for domain, weight in DOMAIN_WEIGHTS.items():
        domain_responses = [r for r in responses if r.domain == domain]
        domain_controls = [c for c in controls.values() if c['domain'] == domain]
        
        # Calculate domain statistics
        completed_controls = len([r for r in domain_responses if r.maturity_level is not None])
        total_controls = len(domain_controls)
        
        # Get domain score details
        domain_score_data = domain_details.get(domain, {})
        
        # Identify strengths and weaknesses
        control_scores = []
        for response in domain_responses:
            if response.calculated_score is not None:
                control_info = controls.get(response.control_id, {})
                control_scores.append({
                    'control_id': response.control_id,
                    'control_name': control_info.get('name', 'Unknown'),
                    'score': response.calculated_score,
                    'maturity_level': response.maturity_level
                })
        
        # Sort by score to identify strengths and weaknesses
        control_scores.sort(key=lambda x: x['score'], reverse=True)
        
        strengths = control_scores[:2] if len(control_scores) >= 2 else control_scores
        weaknesses = control_scores[-2:] if len(control_scores) >= 2 else []
        
        domain_analysis[domain] = {
            'score': domain_score_data.get('score', 0),
            'weight': weight,
            'completion_rate': domain_score_data.get('completion_rate', 0),
            'average_maturity': domain_score_data.get('average_maturity', 0),
            'total_controls': total_controls,
            'completed_controls': completed_controls,
            'strengths': strengths,
            'weaknesses': weaknesses,
            'improvement_priority': 'High' if domain_score_data.get('score', 0) < 60 else 'Medium' if domain_score_data.get('score', 0) < 80 else 'Low'
        }
    
    return domain_analysis

def generate_recommendations(assessment, responses: List[Any], scores: Dict[str, Any]) -> Dict[str, Any]:
    """Generate actionable recommendations"""
    
    recommendations = {
        'immediate_actions': [],
        'short_term_goals': [],
        'long_term_objectives': [],
        'priority_controls': []
    }
    
    overall_score = scores.get('overall_score', 0)
    domain_scores = scores.get('domain_scores', {})
    
    # Immediate actions based on overall score
    if overall_score < 50:
        recommendations['immediate_actions'].extend([
            'Establish basic AI governance framework',
            'Assign dedicated AI compliance personnel',
            'Conduct comprehensive risk assessment',
            'Implement basic AI policy documentation'
        ])
    elif overall_score < 70:
        recommendations['immediate_actions'].extend([
            'Strengthen existing AI governance processes',
            'Improve documentation and evidence collection',
            'Enhance monitoring and review procedures'
        ])
    
    # Domain-specific recommendations
    for domain, score in domain_scores.items():
        if score < 60:
            if domain == 'governance':
                recommendations['immediate_actions'].append('Strengthen AI governance structure and policies')
            elif domain == 'impact_assessment':
                recommendations['immediate_actions'].append('Implement comprehensive AI impact assessment process')
            elif domain == 'development':
                recommendations['immediate_actions'].append('Establish AI development lifecycle controls')
            elif domain == 'operations':
                recommendations['immediate_actions'].append('Improve AI system monitoring and operations')
    
    # Short-term goals (3-6 months)
    recommendations['short_term_goals'].extend([
        'Achieve 80% completion across all assessment stages',
        'Implement automated monitoring for high-risk AI systems',
        'Establish regular compliance review cycles',
        'Train staff on AI governance requirements'
    ])
    
    # Long-term objectives (6-12 months)
    recommendations['long_term_objectives'].extend([
        'Achieve overall compliance score above 80%',
        'Implement continuous improvement processes',
        'Establish AI center of excellence',
        'Integrate AI governance with business processes'
    ])
    
    # Priority controls based on low scores
    low_scoring_responses = [r for r in responses if r.calculated_score is not None and r.calculated_score < 60]
    low_scoring_responses.sort(key=lambda x: x.calculated_score)
    
    from src.utils.scoring import get_iso42001_controls
    controls = get_iso42001_controls()
    
    for response in low_scoring_responses[:5]:  # Top 5 priority controls
        control_info = controls.get(response.control_id, {})
        recommendations['priority_controls'].append({
            'control_id': response.control_id,
            'control_name': control_info.get('name', 'Unknown'),
            'current_score': response.calculated_score,
            'current_maturity': response.maturity_level,
            'target_maturity': min(response.maturity_level + 2, 5) if response.maturity_level else 3,
            'domain': response.domain,
            'stage': response.stage
        })
    
    return recommendations

def generate_detailed_findings(responses: List[Any]) -> Dict[str, Any]:
    """Generate detailed findings for each control"""
    
    from src.utils.scoring import get_iso42001_controls
    controls = get_iso42001_controls()
    
    findings = {}
    
    for response in responses:
        if response.maturity_level is not None:
            control_info = controls.get(response.control_id, {})
            
            # Determine finding status
            if response.calculated_score >= 80:
                status = 'Compliant'
                status_description = 'Control is well implemented and effective'
            elif response.calculated_score >= 60:
                status = 'Partially Compliant'
                status_description = 'Control is implemented but needs improvement'
            else:
                status = 'Non-Compliant'
                status_description = 'Control requires significant improvement or implementation'
            
            findings[response.control_id] = {
                'control_name': control_info.get('name', 'Unknown'),
                'domain': response.domain,
                'stage': response.stage,
                'status': status,
                'status_description': status_description,
                'score': response.calculated_score,
                'maturity_level': response.maturity_level,
                'evidence_completeness': response.evidence_completeness,
                'response_quality': response.response_quality,
                'comments': response.comments,
                'evidence_files_count': len(response.get_evidence_files()),
                'validation_errors': response.get_validation_errors()
            }
    
    return findings

def generate_evidence_summary(responses: List[Any]) -> Dict[str, Any]:
    """Generate evidence collection summary"""
    
    total_files = sum(len(r.get_evidence_files()) for r in responses)
    responses_with_evidence = len([r for r in responses if r.get_evidence_files()])
    total_responses = len([r for r in responses if r.maturity_level is not None])
    
    evidence_coverage = (responses_with_evidence / total_responses * 100) if total_responses > 0 else 0
    
    # Evidence by stage
    stage_evidence = {}
    for response in responses:
        stage = response.stage
        if stage not in stage_evidence:
            stage_evidence[stage] = {'files': 0, 'responses': 0}
        
        stage_evidence[stage]['files'] += len(response.get_evidence_files())
        if response.maturity_level is not None:
            stage_evidence[stage]['responses'] += 1
    
    return {
        'total_evidence_files': total_files,
        'responses_with_evidence': responses_with_evidence,
        'evidence_coverage_percentage': round(evidence_coverage, 1),
        'evidence_by_stage': stage_evidence,
        'average_files_per_response': round(total_files / total_responses, 1) if total_responses > 0 else 0
    }

def generate_technical_details(assessment, responses: List[Any], scores: Dict[str, Any]) -> Dict[str, Any]:
    """Generate technical implementation details"""
    
    return {
        'scoring_methodology': scores.get('calculation_metadata', {}),
        'assessment_configuration': {
            'risk_level': assessment.risk_level,
            'regulatory_requirements': assessment.get_regulatory_requirements(),
            'industry': assessment.industry
        },
        'data_quality_metrics': {
            'response_completeness': scores.get('assessment_completeness', 0),
            'average_evidence_quality': scores.get('average_evidence_quality', 0),
            'confidence_interval': scores.get('confidence_interval', {})
        },
        'validation_summary': generate_validation_summary(responses)
    }

def generate_validation_summary(responses: List[Any]) -> Dict[str, Any]:
    """Generate validation summary for technical details"""
    
    total_responses = len(responses)
    validated_responses = len([r for r in responses if r.is_validated])
    responses_with_errors = len([r for r in responses if r.get_validation_errors()])
    
    return {
        'total_responses': total_responses,
        'validated_responses': validated_responses,
        'validation_rate': round((validated_responses / total_responses * 100) if total_responses > 0 else 0, 1),
        'responses_with_errors': responses_with_errors,
        'error_rate': round((responses_with_errors / total_responses * 100) if total_responses > 0 else 0, 1)
    }

def generate_raw_data_section(assessment, responses: List[Any]) -> Dict[str, Any]:
    """Generate raw data section for technical reports"""
    
    return {
        'assessment_data': assessment.to_dict(include_responses=False),
        'response_data': [response.to_dict() for response in responses],
        'export_timestamp': datetime.utcnow().isoformat(),
        'data_format_version': '1.0'
    }

def get_methodology_description() -> Dict[str, Any]:
    """Get scoring methodology description"""
    
    return {
        'overview': 'ISO 42001 compliance scoring based on maturity levels, evidence quality, and response completeness',
        'maturity_levels': {
            '0': 'Not Implemented - No evidence of implementation',
            '1': 'Ad-hoc/Informal - Basic, informal implementation',
            '2': 'Defined but Inconsistent - Documented but inconsistently applied',
            '3': 'Managed and Implemented - Consistently implemented and managed',
            '4': 'Measured and Monitored - Measured, monitored, and controlled',
            '5': 'Optimized and Continuously Improved - Continuously optimized'
        },
        'scoring_factors': {
            'maturity_level': 'Base score from 0-100 based on maturity level',
            'evidence_completeness': 'Adjustment factor (±10%) based on evidence quality',
            'response_quality': 'Adjustment factor (±5%) based on response detail and completeness'
        },
        'domain_weights': {
            'impact_assessment': '25%',
            'development': '20%',
            'operations': '15%',
            'governance': '15%',
            'resources': '10%',
            'stakeholders': '10%',
            'documentation': '5%'
        }
    }

def get_control_definitions_summary() -> Dict[str, Any]:
    """Get summary of control definitions"""
    
    from src.utils.scoring import get_iso42001_controls
    controls = get_iso42001_controls()
    
    summary = {}
    for control_id, control_info in controls.items():
        summary[control_id] = {
            'name': control_info['name'],
            'domain': control_info['domain'],
            'stage': control_info['stage'],
            'weight': control_info['weight'],
            'description': control_info['description']
        }
    
    return summary

