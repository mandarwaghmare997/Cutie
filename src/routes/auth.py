from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import random
import string
import re

from src.models.user import User, OTPCode, db

auth_bp = Blueprint('auth', __name__)

def generate_otp():
    """Generate a 6-digit OTP code"""
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(email, otp_code, purpose='email_verification'):
    """Send OTP code via email (mock implementation for development)"""
    # In production, this would integrate with AWS SES
    print(f"[EMAIL] Sending OTP {otp_code} to {email} for {purpose}")
    # TODO: Implement actual email sending with SES
    return True

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    return True, "Password is valid"

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user account"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'firstName', 'lastName', 
                          'organizationName', 'industry', 'role', 'country']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                'error': 'validation_error',
                'message': 'Missing required fields',
                'details': [f'{field} is required' for field in missing_fields]
            }), 400
        
        # Validate email format
        email = data['email'].lower().strip()
        if not validate_email(email):
            return jsonify({
                'error': 'validation_error',
                'message': 'Invalid email format'
            }), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({
                'error': 'email_exists',
                'message': 'An account with this email already exists'
            }), 409
        
        # Validate password
        password_valid, password_message = validate_password(data['password'])
        if not password_valid:
            return jsonify({
                'error': 'validation_error',
                'message': password_message
            }), 400
        
        # Create new user
        user = User(
            email=email,
            password=data['password'],
            first_name=data['firstName'],
            last_name=data['lastName'],
            organization_name=data['organizationName'],
            industry=data['industry'],
            role=data['role'],
            phone=data.get('phone'),
            country=data['country']
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Generate and send OTP for email verification
        otp_code = generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=15)  # OTP expires in 15 minutes
        
        otp = OTPCode(
            user_id=user.id,
            code=otp_code,
            purpose='email_verification',
            expires_at=expires_at
        )
        
        db.session.add(otp)
        db.session.commit()
        
        # Send OTP email
        if send_otp_email(email, otp_code, 'email_verification'):
            return jsonify({
                'userId': user.id,
                'email': user.email,
                'status': 'pending_verification',
                'message': 'Registration successful. Please check your email for verification code.'
            }), 201
        else:
            return jsonify({
                'error': 'email_send_failed',
                'message': 'Failed to send verification email. Please try again.'
            }), 500
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Registration error: {str(e)}")
        return jsonify({
            'error': 'internal_error',
            'message': 'An error occurred during registration'
        }), 500

@auth_bp.route('/verify-email', methods=['POST'])
def verify_email():
    """Verify user email with OTP code"""
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('otpCode'):
            return jsonify({
                'error': 'validation_error',
                'message': 'Email and OTP code are required'
            }), 400
        
        email = data['email'].lower().strip()
        otp_code = data['otpCode'].strip()
        
        # Find user
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({
                'error': 'user_not_found',
                'message': 'User not found'
            }), 404
        
        # Find valid OTP
        otp = OTPCode.query.filter_by(
            user_id=user.id,
            code=otp_code,
            purpose='email_verification',
            is_used=False
        ).first()
        
        if not otp:
            return jsonify({
                'error': 'invalid_otp',
                'message': 'Invalid OTP code'
            }), 400
        
        if otp.is_expired():
            return jsonify({
                'error': 'expired_otp',
                'message': 'OTP code has expired'
            }), 400
        
        # Verify user and mark OTP as used
        user.is_verified = True
        user.last_login = datetime.utcnow()
        otp.mark_as_used()
        
        db.session.commit()
        
        # Generate JWT tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        return jsonify({
            'userId': user.id,
            'email': user.email,
            'status': 'verified',
            'accessToken': access_token,
            'refreshToken': refresh_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Email verification error: {str(e)}")
        return jsonify({
            'error': 'internal_error',
            'message': 'An error occurred during email verification'
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return tokens"""
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({
                'error': 'validation_error',
                'message': 'Email and password are required'
            }), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        
        # Find user
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return jsonify({
                'error': 'invalid_credentials',
                'message': 'Invalid email or password'
            }), 401
        
        # Check if user is verified
        if not user.is_verified:
            return jsonify({
                'error': 'account_not_verified',
                'message': 'Please verify your email address before logging in'
            }), 403
        
        # Check if user is active
        if not user.is_active:
            return jsonify({
                'error': 'account_disabled',
                'message': 'Your account has been disabled. Please contact support.'
            }), 403
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Generate JWT tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        return jsonify({
            'userId': user.id,
            'email': user.email,
            'accessToken': access_token,
            'refreshToken': refresh_token,
            'expiresIn': current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds(),
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        return jsonify({
            'error': 'internal_error',
            'message': 'An error occurred during login'
        }), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token using refresh token"""
    try:
        current_user_id = get_jwt_identity()
        
        # Verify user still exists and is active
        user = User.query.get(current_user_id)
        if not user or not user.is_active:
            return jsonify({
                'error': 'invalid_user',
                'message': 'User not found or inactive'
            }), 401
        
        # Generate new access token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'accessToken': access_token,
            'expiresIn': current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Token refresh error: {str(e)}")
        return jsonify({
            'error': 'internal_error',
            'message': 'An error occurred during token refresh'
        }), 500

@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    """Resend OTP code for email verification"""
    try:
        data = request.get_json()
        
        if not data.get('email'):
            return jsonify({
                'error': 'validation_error',
                'message': 'Email is required'
            }), 400
        
        email = data['email'].lower().strip()
        
        # Find user
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({
                'error': 'user_not_found',
                'message': 'User not found'
            }), 404
        
        if user.is_verified:
            return jsonify({
                'error': 'already_verified',
                'message': 'Email is already verified'
            }), 400
        
        # Mark existing OTPs as used
        existing_otps = OTPCode.query.filter_by(
            user_id=user.id,
            purpose='email_verification',
            is_used=False
        ).all()
        
        for otp in existing_otps:
            otp.mark_as_used()
        
        # Generate new OTP
        otp_code = generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=15)
        
        otp = OTPCode(
            user_id=user.id,
            code=otp_code,
            purpose='email_verification',
            expires_at=expires_at
        )
        
        db.session.add(otp)
        db.session.commit()
        
        # Send OTP email
        if send_otp_email(email, otp_code, 'email_verification'):
            return jsonify({
                'message': 'Verification code sent successfully'
            }), 200
        else:
            return jsonify({
                'error': 'email_send_failed',
                'message': 'Failed to send verification email'
            }), 500
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Resend OTP error: {str(e)}")
        return jsonify({
            'error': 'internal_error',
            'message': 'An error occurred while resending OTP'
        }), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({
                'error': 'user_not_found',
                'message': 'User not found'
            }), 404
        
        return jsonify({
            'user': user.to_dict(include_sensitive=True)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get profile error: {str(e)}")
        return jsonify({
            'error': 'internal_error',
            'message': 'An error occurred while fetching profile'
        }), 500

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({
                'error': 'user_not_found',
                'message': 'User not found'
            }), 404
        
        data = request.get_json()
        
        # Update allowed fields
        updatable_fields = ['first_name', 'last_name', 'phone', 'organization_name', 'industry', 'role']
        
        for field in updatable_fields:
            if field in data:
                setattr(user, field, data[field].strip() if data[field] else None)
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update profile error: {str(e)}")
        return jsonify({
            'error': 'internal_error',
            'message': 'An error occurred while updating profile'
        }), 500

