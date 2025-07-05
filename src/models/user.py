from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import bcrypt
import uuid

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    
    # Personal Information
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    country = db.Column(db.String(50), nullable=False)
    
    # Organization Information
    organization_name = db.Column(db.String(200), nullable=False)
    industry = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    
    # Account Status
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    user_role = db.Column(db.String(20), default='user', nullable=False)  # user, admin
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    assessments = db.relationship('Assessment', backref='user', lazy=True, cascade='all, delete-orphan')
    otp_codes = db.relationship('OTPCode', backref='user', lazy=True, cascade='all, delete-orphan')

    def __init__(self, email, password, first_name, last_name, organization_name, industry, role, phone=None, country=None):
        self.email = email.lower().strip()
        self.set_password(password)
        self.first_name = first_name.strip()
        self.last_name = last_name.strip()
        self.organization_name = organization_name.strip()
        self.industry = industry.strip()
        self.role = role.strip()
        self.phone = phone.strip() if phone else None
        self.country = country.strip() if country else None

    def set_password(self, password):
        """Hash and set the user's password"""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def check_password(self, password):
        """Check if the provided password matches the user's password"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def get_full_name(self):
        """Get the user's full name"""
        return f"{self.first_name} {self.last_name}"

    def to_dict(self, include_sensitive=False):
        """Convert user object to dictionary"""
        data = {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.get_full_name(),
            'phone': self.phone,
            'country': self.country,
            'organization_name': self.organization_name,
            'industry': self.industry,
            'role': self.role,
            'is_verified': self.is_verified,
            'is_active': self.is_active,
            'user_role': self.user_role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
        
        if include_sensitive:
            data['assessment_count'] = len(self.assessments)
            
        return data

    def __repr__(self):
        return f'<User {self.email}>'


class OTPCode(db.Model):
    __tablename__ = 'otp_codes'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    code = db.Column(db.String(6), nullable=False)
    purpose = db.Column(db.String(50), nullable=False)  # email_verification, password_reset
    is_used = db.Column(db.Boolean, default=False, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __init__(self, user_id, code, purpose, expires_at):
        self.user_id = user_id
        self.code = code
        self.purpose = purpose
        self.expires_at = expires_at

    def is_expired(self):
        """Check if the OTP code has expired"""
        return datetime.utcnow() > self.expires_at

    def is_valid(self):
        """Check if the OTP code is valid (not used and not expired)"""
        return not self.is_used and not self.is_expired()

    def mark_as_used(self):
        """Mark the OTP code as used"""
        self.is_used = True
        db.session.commit()

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'purpose': self.purpose,
            'is_used': self.is_used,
            'expires_at': self.expires_at.isoformat(),
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<OTPCode {self.code} for {self.user_id}>'

