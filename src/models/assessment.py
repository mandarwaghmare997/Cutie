from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
import json

db = SQLAlchemy()

class Assessment(db.Model):
    __tablename__ = 'assessments'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # Assessment Metadata
    assessment_name = db.Column(db.String(200), nullable=False)
    organization_name = db.Column(db.String(200), nullable=False)
    ai_system_description = db.Column(db.Text, nullable=False)
    industry = db.Column(db.String(100), nullable=False)
    risk_level = db.Column(db.String(20), nullable=False)  # low, medium, high
    
    # Status and Progress
    status = db.Column(db.String(50), default='in_progress', nullable=False)  # in_progress, completed, archived
    current_stage = db.Column(db.String(50), default='requirements_gathering', nullable=False)
    
    # Progress Tracking (JSON field)
    progress = db.Column(db.Text, nullable=False, default='{}')
    
    # Scoring Results (JSON field)
    scores = db.Column(db.Text, nullable=True)
    
    # Regulatory Requirements (JSON field)
    regulatory_requirements = db.Column(db.Text, nullable=True, default='[]')
    
    # Certificate information
    certificate_generated = db.Column(db.Boolean, default=False, nullable=False)
    certificate_id = db.Column(db.String(100), nullable=True, unique=True)
    certificate_generated_at = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    responses = db.relationship('AssessmentResponse', backref='assessment', lazy=True, cascade='all, delete-orphan')
    files = db.relationship('AssessmentFile', backref='assessment', lazy=True, cascade='all, delete-orphan')

    def __init__(self, user_id, assessment_name, organization_name, ai_system_description, 
                 industry, risk_level, regulatory_requirements=None):
        self.user_id = user_id
        self.assessment_name = assessment_name.strip()
        self.organization_name = organization_name.strip()
        self.ai_system_description = ai_system_description.strip()
        self.industry = industry.strip()
        self.risk_level = risk_level.lower()
        self.regulatory_requirements = json.dumps(regulatory_requirements or [])
        self.progress = json.dumps({
            'overall': 0,
            'stages': {
                'requirements_gathering': 0,
                'gap_assessment': 0,
                'policy_review': 0,
                'implementation_status': 0,
                'internal_audit': 0
            }
        })

    def get_progress(self):
        """Get progress data as dictionary"""
        try:
            return json.loads(self.progress)
        except (json.JSONDecodeError, TypeError):
            return {
                'overall': 0,
                'stages': {
                    'requirements_gathering': 0,
                    'gap_assessment': 0,
                    'policy_review': 0,
                    'implementation_status': 0,
                    'internal_audit': 0
                }
            }

    def set_progress(self, progress_data):
        """Set progress data from dictionary"""
        self.progress = json.dumps(progress_data)

    def get_scores(self):
        """Get scores data as dictionary"""
        if not self.scores:
            return None
        try:
            return json.loads(self.scores)
        except (json.JSONDecodeError, TypeError):
            return None

    def set_scores(self, scores_data):
        """Set scores data from dictionary"""
        self.scores = json.dumps(scores_data)

    def get_regulatory_requirements(self):
        """Get regulatory requirements as list"""
        try:
            return json.loads(self.regulatory_requirements)
        except (json.JSONDecodeError, TypeError):
            return []

    def set_regulatory_requirements(self, requirements):
        """Set regulatory requirements from list"""
        self.regulatory_requirements = json.dumps(requirements or [])

    def update_stage_progress(self, stage, progress_percentage):
        """Update progress for a specific stage"""
        progress_data = self.get_progress()
        progress_data['stages'][stage] = progress_percentage
        
        # Calculate overall progress
        stage_weights = {
            'requirements_gathering': 0.2,
            'gap_assessment': 0.25,
            'policy_review': 0.2,
            'implementation_status': 0.25,
            'internal_audit': 0.1
        }
        
        overall = sum(progress_data['stages'][stage] * weight 
                     for stage, weight in stage_weights.items())
        progress_data['overall'] = round(overall, 1)
        
        self.set_progress(progress_data)

    def advance_stage(self):
        """Advance to the next assessment stage"""
        stage_order = [
            'requirements_gathering',
            'gap_assessment', 
            'policy_review',
            'implementation_status',
            'internal_audit'
        ]
        
        current_index = stage_order.index(self.current_stage)
        if current_index < len(stage_order) - 1:
            self.current_stage = stage_order[current_index + 1]
            return True
        return False

    def complete_assessment(self):
        """Mark assessment as completed"""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()

    def to_dict(self, include_responses=False):
        """Convert assessment to dictionary"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'assessment_name': self.assessment_name,
            'organization_name': self.organization_name,
            'ai_system_description': self.ai_system_description,
            'industry': self.industry,
            'risk_level': self.risk_level,
            'status': self.status,
            'current_stage': self.current_stage,
            'progress': self.get_progress(),
            'scores': self.get_scores(),
            'regulatory_requirements': self.get_regulatory_requirements(),
            'certificate_generated': self.certificate_generated,
            'certificate_id': self.certificate_id,
            'certificate_generated_at': self.certificate_generated_at.isoformat() if self.certificate_generated_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'response_count': len(self.responses),
            'file_count': len(self.files)
        }
        
        if include_responses:
            data['responses'] = [response.to_dict() for response in self.responses]
            
        return data

    def __repr__(self):
        return f'<Assessment {self.assessment_name} for {self.user_id}>'


class AssessmentResponse(db.Model):
    __tablename__ = 'assessment_responses'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_id = db.Column(db.String(36), db.ForeignKey('assessments.id'), nullable=False)
    
    # Control Information
    control_id = db.Column(db.String(20), nullable=False)  # e.g., A.2.2, A.3.2
    stage = db.Column(db.String(50), nullable=False)
    domain = db.Column(db.String(50), nullable=False)
    
    # Response Data (JSON field)
    responses = db.Column(db.Text, nullable=False, default='{}')
    
    # Assessment Results
    maturity_level = db.Column(db.Integer, nullable=True)  # 0-5
    evidence_completeness = db.Column(db.Float, nullable=True)  # 0.0-1.0
    response_quality = db.Column(db.Float, nullable=True)  # 0.0-1.0
    calculated_score = db.Column(db.Float, nullable=True)  # 0.0-100.0
    
    # Additional Information
    comments = db.Column(db.Text, nullable=True)
    evidence_files = db.Column(db.Text, nullable=True, default='[]')  # JSON array of file IDs
    
    # Validation
    is_validated = db.Column(db.Boolean, default=False, nullable=False)
    validation_errors = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __init__(self, assessment_id, control_id, stage, domain):
        self.assessment_id = assessment_id
        self.control_id = control_id
        self.stage = stage
        self.domain = domain

    def get_responses(self):
        """Get responses data as dictionary"""
        try:
            return json.loads(self.responses)
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_responses(self, responses_data):
        """Set responses data from dictionary"""
        self.responses = json.dumps(responses_data)

    def get_evidence_files(self):
        """Get evidence files as list"""
        try:
            return json.loads(self.evidence_files)
        except (json.JSONDecodeError, TypeError):
            return []

    def set_evidence_files(self, file_ids):
        """Set evidence files from list"""
        self.evidence_files = json.dumps(file_ids or [])

    def add_evidence_file(self, file_id):
        """Add an evidence file ID"""
        files = self.get_evidence_files()
        if file_id not in files:
            files.append(file_id)
            self.set_evidence_files(files)

    def get_validation_errors(self):
        """Get validation errors as list"""
        if not self.validation_errors:
            return []
        try:
            return json.loads(self.validation_errors)
        except (json.JSONDecodeError, TypeError):
            return []

    def set_validation_errors(self, errors):
        """Set validation errors from list"""
        self.validation_errors = json.dumps(errors or [])

    def validate_response(self):
        """Validate the response data"""
        errors = []
        responses_data = self.get_responses()
        
        # Check if required questions are answered
        if not responses_data.get('questions'):
            errors.append("No responses provided to assessment questions")
        
        # Check maturity level
        if self.maturity_level is None or not (0 <= self.maturity_level <= 5):
            errors.append("Invalid maturity level (must be 0-5)")
        
        # Set validation results
        self.set_validation_errors(errors)
        self.is_validated = len(errors) == 0
        
        return self.is_validated

    def to_dict(self):
        """Convert response to dictionary"""
        return {
            'id': self.id,
            'assessment_id': self.assessment_id,
            'control_id': self.control_id,
            'stage': self.stage,
            'domain': self.domain,
            'responses': self.get_responses(),
            'maturity_level': self.maturity_level,
            'evidence_completeness': self.evidence_completeness,
            'response_quality': self.response_quality,
            'calculated_score': self.calculated_score,
            'comments': self.comments,
            'evidence_files': self.get_evidence_files(),
            'is_validated': self.is_validated,
            'validation_errors': self.get_validation_errors(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def __repr__(self):
        return f'<AssessmentResponse {self.control_id} for {self.assessment_id}>'


class AssessmentFile(db.Model):
    __tablename__ = 'assessment_files'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_id = db.Column(db.String(36), db.ForeignKey('assessments.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # File Information
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    file_type = db.Column(db.String(100), nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    
    # Control Association
    control_id = db.Column(db.String(20), nullable=True)
    stage = db.Column(db.String(50), nullable=True)
    
    # File Status
    scan_status = db.Column(db.String(20), default='pending', nullable=False)  # pending, clean, infected
    is_processed = db.Column(db.Boolean, default=False, nullable=False)
    
    # Metadata
    description = db.Column(db.Text, nullable=True)
    file_metadata = db.Column(db.Text, nullable=True, default='{}')  # JSON field for additional metadata
    
    # Timestamps
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    processed_at = db.Column(db.DateTime, nullable=True)

    def __init__(self, assessment_id, user_id, original_filename, stored_filename, 
                 file_path, file_size, file_type, mime_type, control_id=None, stage=None, description=None):
        self.assessment_id = assessment_id
        self.user_id = user_id
        self.original_filename = original_filename
        self.stored_filename = stored_filename
        self.file_path = file_path
        self.file_size = file_size
        self.file_type = file_type
        self.mime_type = mime_type
        self.control_id = control_id
        self.stage = stage
        self.description = description

    def get_metadata(self):
        """Get metadata as dictionary"""
        try:
            return json.loads(self.file_metadata)
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_metadata(self, metadata_dict):
        """Set metadata from dictionary"""
        self.file_metadata = json.dumps(metadata_dict or {})

    def mark_as_clean(self):
        """Mark file as clean after virus scan"""
        self.scan_status = 'clean'
        self.is_processed = True
        self.processed_at = datetime.utcnow()

    def mark_as_infected(self):
        """Mark file as infected"""
        self.scan_status = 'infected'
        self.is_processed = True
        self.processed_at = datetime.utcnow()

    def to_dict(self):
        """Convert file to dictionary"""
        return {
            'id': self.id,
            'assessment_id': self.assessment_id,
            'user_id': self.user_id,
            'original_filename': self.original_filename,
            'stored_filename': self.stored_filename,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'mime_type': self.mime_type,
            'control_id': self.control_id,
            'stage': self.stage,
            'scan_status': self.scan_status,
            'is_processed': self.is_processed,
            'description': self.description,
            'file_metadata': self.get_metadata(),
            'uploaded_at': self.uploaded_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }

    def __repr__(self):
        return f'<AssessmentFile {self.original_filename} for {self.assessment_id}>'

