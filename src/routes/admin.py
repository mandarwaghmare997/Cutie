from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import func, desc

from src.models.user import User, db
from src.models.assessment import Assessment, AssessmentResponse, AssessmentFile

admin_bp = Blueprint('admin', __name__)

def require_admin():
    """Decorator to require admin role"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user or user.user_role != 'admin':
                return jsonify({
                    'error': 'access_denied',
                    'message': 'Admin access required'
                }), 403
            
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@require_admin()
def get_dashboard_stats():
    """Get admin dashboard statistics"""
    try:
        # User statistics
        total_users = User.query.count()
        verified_users = User.query.filter_by(is_verified=True).count()
        active_users = User.query.filter_by(is_active=True).count()
        
        # Recent user registrations (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_registrations = User.query.filter(
            User.created_at >= thirty_days_ago
        ).count()
        
        # Assessment statistics
        total_assessments = Assessment.query.count()
        completed_assessments = Assessment.query.filter_by(status='completed').count()
        in_progress_assessments = Assessment.query.filter_by(status='in_progress').count()
        
        # Recent assessments (last 30 days)
        recent_assessments = Assessment.query.filter(
            Assessment.created_at >= thirty_days_ago
        ).count()
        
        # File statistics
        total_files = AssessmentFile.query.count()
        total_file_size = db.session.query(
            func.sum(AssessmentFile.file_size)
        ).scalar() or 0
        
        # Industry distribution
        industry_stats = db.session.query(
            User.industry,
            func.count(User.id).label('count')
        ).group_by(User.industry).all()
        
        # Risk level distribution
        risk_stats = db.session.query(
            Assessment.risk_level,
            func.count(Assessment.id).label('count')
        ).group_by(Assessment.risk_level).all()
        
        # Assessment completion rate by stage
        stage_stats = db.session.query(
            Assessment.current_stage,
            func.count(Assessment.id).label('count')
        ).group_by(Assessment.current_stage).all()
        
        return jsonify({
            'users': {
                'total': total_users,
                'verified': verified_users,
                'active': active_users,
                'recent_registrations': recent_registrations,
                'verification_rate': round((verified_users / total_users * 100) if total_users > 0 else 0, 1)
            },
            'assessments': {
                'total': total_assessments,
                'completed': completed_assessments,
                'in_progress': in_progress_assessments,
                'recent': recent_assessments,
                'completion_rate': round((completed_assessments / total_assessments * 100) if total_assessments > 0 else 0, 1)
            },
            'files': {
                'total': total_files,
                'total_size_mb': round(total_file_size / (1024 * 1024), 2),
                'average_size_kb': round((total_file_size / total_files / 1024) if total_files > 0 else 0, 2)
            },
            'distributions': {
                'industries': [{'industry': industry, 'count': count} for industry, count in industry_stats],
                'risk_levels': [{'risk_level': risk_level, 'count': count} for risk_level, count in risk_stats],
                'assessment_stages': [{'stage': stage, 'count': count} for stage, count in stage_stats]
            },
            'generated_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Dashboard stats error: {str(e)}")
        return jsonify({
            'error': 'internal_error',
            'message': 'An error occurred while fetching dashboard statistics'
        }), 500

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@require_admin()
def get_users():
    """Get all users with pagination and filtering"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        search = request.args.get('search', '')
        industry = request.args.get('industry', '')
        verified = request.args.get('verified', '')
        active = request.args.get('active', '')
        
        # Build query
        query = User.query
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    User.email.ilike(search_term),
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term),
                    User.organization_name.ilike(search_term)
                )
            )
        
        if industry:
            query = query.filter_by(industry=industry)
        
        if verified:
            query = query.filter_by(is_verified=verified.lower() == 'true')
        
        if active:
            query = query.filter_by(is_active=active.lower() == 'true')
        
        # Apply pagination
        pagination = query.order_by(desc(User.created_at)).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        users = pagination.items
        
        return jsonify({
            'users': [user.to_dict(include_sensitive=True) for user in users],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get users error: {str(e)}")
        return jsonify({
            'error': 'internal_error',
            'message': 'An error occurred while fetching users'
        }), 500

@admin_bp.route('/users/<user_id>', methods=['GET'])
@jwt_required()
@require_admin()
def get_user_details(user_id):
    """Get detailed user information"""
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'error': 'user_not_found',
                'message': 'User not found'
            }), 404
        
        # Get user's assessments
        assessments = Assessment.query.filter_by(user_id=user_id).all()
        
        # Get assessment statistics
        assessment_stats = {
            'total': len(assessments),
            'completed': len([a for a in assessments if a.status == 'completed']),
            'in_progress': len([a for a in assessments if a.status == 'in_progress']),
            'average_score': 0
        }
        
        # Calculate average score for completed assessments
        completed_with_scores = [a for a in assessments if a.status == 'completed' and a.get_scores()]
        if completed_with_scores:
            total_score = sum(a.get_scores().get('overall_score', 0) for a in completed_with_scores)
            assessment_stats['average_score'] = round(total_score / len(completed_with_scores), 1)
        
        return jsonify({
            'user': user.to_dict(include_sensitive=True),
            'assessments': [assessment.to_dict() for assessment in assessments],
            'assessment_stats': assessment_stats
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get user details error: {str(e)}")
        return jsonify({
            'error': 'internal_error',
            'message': 'An error occurred while fetching user details'
        }), 500

@admin_bp.route('/users/<user_id>/toggle-status', methods=['POST'])
@jwt_required()
@require_admin()
def toggle_user_status(user_id):
    """Toggle user active status"""
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'error': 'user_not_found',
                'message': 'User not found'
            }), 404
        
        # Don't allow deactivating admin users
        if user.user_role == 'admin' and user.is_active:
            return jsonify({
                'error': 'cannot_deactivate_admin',
                'message': 'Cannot deactivate admin users'
            }), 400
        
        user.is_active = not user.is_active
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': f"User {'activated' if user.is_active else 'deactivated'} successfully",
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Toggle user status error: {str(e)}")
        return jsonify({
            'error': 'internal_error',
            'message': 'An error occurred while updating user status'
        }), 500

@admin_bp.route('/assessments', methods=['GET'])
@jwt_required()
@require_admin()
def get_all_assessments():
    """Get all assessments with pagination and filtering"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        status = request.args.get('status', '')
        risk_level = request.args.get('risk_level', '')
        industry = request.args.get('industry', '')
        
        # Build query with user join for filtering
        query = db.session.query(Assessment).join(User)
        
        if status:
            query = query.filter(Assessment.status == status)
        
        if risk_level:
            query = query.filter(Assessment.risk_level == risk_level)
        
        if industry:
            query = query.filter(User.industry == industry)
        
        # Apply pagination
        pagination = query.order_by(desc(Assessment.created_at)).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        assessments = pagination.items
        
        # Get user information for each assessment
        assessment_data = []
        for assessment in assessments:
            assessment_dict = assessment.to_dict()
            user = User.query.get(assessment.user_id)
            assessment_dict['user_info'] = {
                'email': user.email,
                'organization_name': user.organization_name,
                'industry': user.industry
            } if user else None
            assessment_data.append(assessment_dict)
        
        return jsonify({
            'assessments': assessment_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get all assessments error: {str(e)}")
        return jsonify({
            'error': 'internal_error',
            'message': 'An error occurred while fetching assessments'
        }), 500

@admin_bp.route('/analytics/compliance-trends', methods=['GET'])
@jwt_required()
@require_admin()
def get_compliance_trends():
    """Get compliance score trends and analytics"""
    try:
        # Get query parameters
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get completed assessments with scores
        completed_assessments = Assessment.query.filter(
            Assessment.status == 'completed',
            Assessment.completed_at >= start_date,
            Assessment.scores.isnot(None)
        ).all()
        
        # Calculate trends
        trends = []
        score_data = []
        
        for assessment in completed_assessments:
            scores = assessment.get_scores()
            if scores and 'overall_score' in scores:
                score_data.append({
                    'date': assessment.completed_at.isoformat(),
                    'score': scores['overall_score'],
                    'risk_level': assessment.risk_level,
                    'industry': assessment.industry
                })
        
        # Calculate average scores by industry
        industry_scores = {}
        for data in score_data:
            industry = data['industry']
            if industry not in industry_scores:
                industry_scores[industry] = []
            industry_scores[industry].append(data['score'])
        
        industry_averages = {
            industry: round(sum(scores) / len(scores), 1)
            for industry, scores in industry_scores.items()
        }
        
        # Calculate average scores by risk level
        risk_scores = {}
        for data in score_data:
            risk_level = data['risk_level']
            if risk_level not in risk_scores:
                risk_scores[risk_level] = []
            risk_scores[risk_level].append(data['score'])
        
        risk_averages = {
            risk_level: round(sum(scores) / len(scores), 1)
            for risk_level, scores in risk_scores.items()
        }
        
        # Overall statistics
        all_scores = [data['score'] for data in score_data]
        overall_stats = {
            'total_assessments': len(completed_assessments),
            'average_score': round(sum(all_scores) / len(all_scores), 1) if all_scores else 0,
            'min_score': min(all_scores) if all_scores else 0,
            'max_score': max(all_scores) if all_scores else 0,
            'score_distribution': {
                'excellent': len([s for s in all_scores if s >= 90]),
                'good': len([s for s in all_scores if 70 <= s < 90]),
                'fair': len([s for s in all_scores if 50 <= s < 70]),
                'poor': len([s for s in all_scores if s < 50])
            }
        }
        
        return jsonify({
            'trends': score_data,
            'industry_averages': industry_averages,
            'risk_level_averages': risk_averages,
            'overall_stats': overall_stats,
            'period_days': days,
            'generated_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get compliance trends error: {str(e)}")
        return jsonify({
            'error': 'internal_error',
            'message': 'An error occurred while fetching compliance trends'
        }), 500

@admin_bp.route('/system/health', methods=['GET'])
@jwt_required()
@require_admin()
def get_system_health():
    """Get system health and performance metrics"""
    try:
        # Database health
        try:
            db.session.execute('SELECT 1')
            db_status = 'healthy'
        except Exception:
            db_status = 'unhealthy'
        
        # File system health
        upload_dir = current_app.config['UPLOAD_FOLDER']
        try:
            if os.path.exists(upload_dir):
                # Check disk space (simplified)
                import shutil
                total, used, free = shutil.disk_usage(upload_dir)
                disk_usage = {
                    'total_gb': round(total / (1024**3), 2),
                    'used_gb': round(used / (1024**3), 2),
                    'free_gb': round(free / (1024**3), 2),
                    'usage_percent': round((used / total) * 100, 1)
                }
                fs_status = 'healthy'
            else:
                disk_usage = None
                fs_status = 'unhealthy'
        except Exception:
            disk_usage = None
            fs_status = 'unhealthy'
        
        # Application metrics
        app_metrics = {
            'uptime': 'N/A',  # Would need to track application start time
            'memory_usage': 'N/A',  # Would need process monitoring
            'active_connections': 'N/A'  # Would need connection tracking
        }
        
        return jsonify({
            'overall_status': 'healthy' if db_status == 'healthy' and fs_status == 'healthy' else 'degraded',
            'database': {
                'status': db_status,
                'connection': 'active'
            },
            'file_system': {
                'status': fs_status,
                'disk_usage': disk_usage
            },
            'application': app_metrics,
            'checked_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"System health check error: {str(e)}")
        return jsonify({
            'error': 'internal_error',
            'message': 'An error occurred while checking system health'
        }), 500


# Additional endpoints for enhanced admin dashboard

@admin_bp.route('/stats', methods=['GET'])
@jwt_required()
@require_admin()
def get_enhanced_stats():
    """Get enhanced statistics for admin dashboard"""
    try:
        # Get basic counts
        total_users = User.query.count()
        total_assessments = Assessment.query.count()
        total_certificates = Assessment.query.filter_by(certificate_generated=True).count()
        
        # Get average compliance score
        avg_score_result = db.session.query(func.avg(Assessment.final_score)).filter(
            Assessment.final_score.isnot(None)
        ).scalar()
        avg_compliance_score = float(avg_score_result) if avg_score_result else 0
        
        # Get user registration trend (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        user_trend_data = []
        user_trend_labels = []
        
        for i in range(30):
            date = thirty_days_ago + timedelta(days=i)
            next_date = date + timedelta(days=1)
            
            daily_users = User.query.filter(
                User.created_at >= date,
                User.created_at < next_date
            ).count()
            
            user_trend_data.append(daily_users)
            user_trend_labels.append(date.strftime('%m/%d'))
        
        # Get assessment status distribution
        status_counts = db.session.query(
            Assessment.status,
            func.count(Assessment.id)
        ).group_by(Assessment.status).all()
        
        assessment_status = [0, 0, 0, 0]  # [completed, in_progress, not_started, on_hold]
        status_map = {
            'completed': 0,
            'in_progress': 1,
            'not_started': 2,
            'on_hold': 3
        }
        
        for status, count in status_counts:
            if status in status_map:
                assessment_status[status_map[status]] = count
        
        return jsonify({
            'totalUsers': total_users,
            'totalAssessments': total_assessments,
            'totalCertificates': total_certificates,
            'avgComplianceScore': avg_compliance_score,
            'userTrend': {
                'labels': user_trend_labels,
                'data': user_trend_data
            },
            'assessmentStatus': assessment_status
        })
        
    except Exception as e:
        current_app.logger.error(f"Enhanced stats error: {str(e)}")
        return jsonify({'error': f'Failed to get admin stats: {str(e)}'}), 500

@admin_bp.route('/activity', methods=['GET'])
@jwt_required()
@require_admin()
def get_recent_activity():
    """Get recent platform activity"""
    try:
        limit = int(request.args.get('limit', 10))
        
        activities = []
        
        # Recent user registrations
        recent_users = User.query.order_by(desc(User.created_at)).limit(limit//3).all()
        for user in recent_users:
            activities.append({
                'type': 'user',
                'description': f'New user registered: {user.first_name} {user.last_name} from {user.organization_name}',
                'timestamp': user.created_at.isoformat()
            })
        
        # Recent assessment completions
        recent_assessments = Assessment.query.filter(
            Assessment.status == 'completed'
        ).order_by(desc(Assessment.completed_at)).limit(limit//3).all()
        
        for assessment in recent_assessments:
            activities.append({
                'type': 'assessment',
                'description': f'Assessment completed: {assessment.name} by {assessment.organization_name}',
                'timestamp': assessment.completed_at.isoformat() if assessment.completed_at else assessment.updated_at.isoformat()
            })
        
        # Recent certificate generations
        recent_certificates = Assessment.query.filter(
            Assessment.certificate_generated == True
        ).order_by(desc(Assessment.certificate_generated_at)).limit(limit//3).all()
        
        for cert in recent_certificates:
            activities.append({
                'type': 'certificate',
                'description': f'Certificate issued: {cert.certificate_id} for {cert.organization_name}',
                'timestamp': cert.certificate_generated_at.isoformat() if cert.certificate_generated_at else cert.updated_at.isoformat()
            })
        
        # Sort by timestamp and limit
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        activities = activities[:limit]
        
        return jsonify({'activities': activities})
        
    except Exception as e:
        current_app.logger.error(f"Recent activity error: {str(e)}")
        return jsonify({'error': f'Failed to get recent activity: {str(e)}'}), 500

@admin_bp.route('/certificates', methods=['GET'])
@jwt_required()
@require_admin()
def get_certificates():
    """Get paginated list of certificates with filters"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        search = request.args.get('search', '').strip()
        date_filter = request.args.get('date', '').strip()
        
        # Build query for assessments with certificates
        query = Assessment.query.filter(Assessment.certificate_generated == True)
        
        # Apply filters
        if search:
            from sqlalchemy import or_
            search_filter = or_(
                Assessment.certificate_id.ilike(f'%{search}%'),
                Assessment.organization_name.ilike(f'%{search}%'),
                Assessment.ai_system_name.ilike(f'%{search}%')
            )
            query = query.filter(search_filter)
        
        if date_filter:
            days = int(date_filter)
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(Assessment.certificate_generated_at >= cutoff_date)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        assessments = query.order_by(desc(Assessment.certificate_generated_at)).offset((page - 1) * limit).limit(limit).all()
        
        # Format certificate data
        certificates = []
        for assessment in assessments:
            cert_data = {
                'assessmentId': assessment.id,
                'certificateId': assessment.certificate_id,
                'organizationName': assessment.organization_name,
                'aiSystemName': assessment.ai_system_name,
                'complianceScore': assessment.final_score,
                'riskLevel': assessment.risk_level,
                'industry': assessment.industry,
                'issuedDate': assessment.certificate_generated_at.isoformat() if assessment.certificate_generated_at else None,
                'validUntil': (assessment.certificate_generated_at + timedelta(days=365)).isoformat() if assessment.certificate_generated_at else None,
                'status': 'Valid'
            }
            certificates.append(cert_data)
        
        return jsonify({
            'certificates': certificates,
            'total': total,
            'page': page,
            'limit': limit,
            'totalPages': (total + limit - 1) // limit
        })
        
    except Exception as e:
        current_app.logger.error(f"Get certificates error: {str(e)}")
        return jsonify({'error': f'Failed to get certificates: {str(e)}'}), 500

@admin_bp.route('/analytics', methods=['GET'])
@jwt_required()
@require_admin()
def get_analytics():
    """Get advanced analytics data"""
    try:
        # Industry breakdown
        industry_data = db.session.query(
            Assessment.industry,
            func.count(Assessment.id).label('count'),
            func.avg(Assessment.final_score).label('avg_score')
        ).filter(Assessment.industry.isnot(None)).group_by(Assessment.industry).all()
        
        # Risk level distribution
        risk_data = db.session.query(
            Assessment.risk_level,
            func.count(Assessment.id)
        ).group_by(Assessment.risk_level).all()
        
        # Monthly certificate issuance (last 12 months)
        twelve_months_ago = datetime.utcnow() - timedelta(days=365)
        monthly_certs = []
        monthly_labels = []
        
        for i in range(12):
            month_start = twelve_months_ago + timedelta(days=30*i)
            month_end = month_start + timedelta(days=30)
            
            cert_count = Assessment.query.filter(
                Assessment.certificate_generated == True,
                Assessment.certificate_generated_at >= month_start,
                Assessment.certificate_generated_at < month_end
            ).count()
            
            monthly_certs.append(cert_count)
            monthly_labels.append(month_start.strftime('%b %Y'))
        
        # Compliance score distribution
        score_ranges = [
            (90, 100, 'Excellent'),
            (80, 89, 'Good'),
            (70, 79, 'Satisfactory'),
            (0, 69, 'Needs Improvement')
        ]
        
        score_distribution = []
        for min_score, max_score, label in score_ranges:
            count = Assessment.query.filter(
                Assessment.final_score >= min_score,
                Assessment.final_score <= max_score
            ).count()
            score_distribution.append({'label': label, 'count': count})
        
        return jsonify({
            'industryBreakdown': [
                {'industry': industry, 'count': count, 'avgScore': float(avg_score) if avg_score else 0}
                for industry, count, avg_score in industry_data
            ],
            'riskDistribution': [
                {'riskLevel': risk_level, 'count': count}
                for risk_level, count in risk_data
            ],
            'monthlyCertificates': {
                'labels': monthly_labels,
                'data': monthly_certs
            },
            'scoreDistribution': score_distribution
        })
        
    except Exception as e:
        current_app.logger.error(f"Analytics error: {str(e)}")
        return jsonify({'error': f'Failed to get analytics: {str(e)}'}), 500

@admin_bp.route('/export/<data_type>', methods=['POST'])
@jwt_required()
@require_admin()
def export_data(data_type):
    """Export data as CSV"""
    try:
        import csv
        import io
        
        filters = request.get_json() or {}
        
        if data_type == 'users':
            return export_users_csv(filters)
        elif data_type == 'assessments':
            return export_assessments_csv(filters)
        elif data_type == 'certificates':
            return export_certificates_csv(filters)
        else:
            return jsonify({'error': 'Invalid data type'}), 400
            
    except Exception as e:
        current_app.logger.error(f"Export error: {str(e)}")
        return jsonify({'error': f'Failed to export data: {str(e)}'}), 500

def export_users_csv(filters):
    """Export users data as CSV"""
    import csv
    import io
    from sqlalchemy import or_
    
    query = User.query
    
    # Apply filters
    if filters.get('search'):
        search = filters['search']
        search_filter = or_(
            User.first_name.ilike(f'%{search}%'),
            User.last_name.ilike(f'%{search}%'),
            User.email.ilike(f'%{search}%'),
            User.organization_name.ilike(f'%{search}%')
        )
        query = query.filter(search_filter)
    
    if filters.get('status'):
        if filters['status'] == 'active':
            query = query.filter(User.is_active == True)
        elif filters['status'] == 'inactive':
            query = query.filter(User.is_active == False)
    
    if filters.get('industry'):
        query = query.filter(User.industry == filters['industry'])
    
    users = query.order_by(desc(User.created_at)).all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'ID', 'First Name', 'Last Name', 'Email', 'Organization', 
        'Industry', 'Role', 'Country', 'Active', 'Created At', 'Last Login'
    ])
    
    # Write data
    for user in users:
        writer.writerow([
            user.id,
            user.first_name,
            user.last_name,
            user.email,
            user.organization_name or '',
            user.industry or '',
            user.user_role or '',
            user.country or '',
            'Yes' if user.is_active else 'No',
            user.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            user.last_login_at.strftime('%Y-%m-%d %H:%M:%S') if user.last_login_at else 'Never'
        ])
    
    output.seek(0)
    return output.getvalue()

def export_assessments_csv(filters):
    """Export assessments data as CSV"""
    import csv
    import io
    from sqlalchemy import or_
    
    query = Assessment.query
    
    # Apply filters
    if filters.get('search'):
        search = filters['search']
        search_filter = or_(
            Assessment.name.ilike(f'%{search}%'),
            Assessment.organization_name.ilike(f'%{search}%'),
            Assessment.ai_system_name.ilike(f'%{search}%')
        )
        query = query.filter(search_filter)
    
    if filters.get('status'):
        query = query.filter(Assessment.status == filters['status'])
    
    if filters.get('risk'):
        query = query.filter(Assessment.risk_level == filters['risk'])
    
    assessments = query.order_by(desc(Assessment.created_at)).all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'ID', 'Name', 'Organization', 'AI System', 'Risk Level', 'Status',
        'Progress', 'Final Score', 'Certificate Generated', 'Created At', 'Completed At'
    ])
    
    # Write data
    for assessment in assessments:
        progress = assessment.get_progress()
        writer.writerow([
            assessment.id,
            assessment.name,
            assessment.organization_name,
            assessment.ai_system_name,
            assessment.risk_level,
            assessment.status,
            f"{progress.get('overall', 0):.1f}%",
            f"{assessment.final_score:.1f}%" if assessment.final_score else '',
            'Yes' if assessment.certificate_generated else 'No',
            assessment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            assessment.completed_at.strftime('%Y-%m-%d %H:%M:%S') if assessment.completed_at else ''
        ])
    
    output.seek(0)
    return output.getvalue()

def export_certificates_csv(filters):
    """Export certificates data as CSV"""
    import csv
    import io
    from sqlalchemy import or_
    
    query = Assessment.query.filter(Assessment.certificate_generated == True)
    
    # Apply filters
    if filters.get('search'):
        search = filters['search']
        search_filter = or_(
            Assessment.certificate_id.ilike(f'%{search}%'),
            Assessment.organization_name.ilike(f'%{search}%'),
            Assessment.ai_system_name.ilike(f'%{search}%')
        )
        query = query.filter(search_filter)
    
    if filters.get('date'):
        days = int(filters['date'])
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(Assessment.certificate_generated_at >= cutoff_date)
    
    assessments = query.order_by(desc(Assessment.certificate_generated_at)).all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Certificate ID', 'Organization', 'AI System', 'Compliance Score',
        'Risk Level', 'Industry', 'Issued Date', 'Valid Until', 'Status'
    ])
    
    # Write data
    for assessment in assessments:
        valid_until = assessment.certificate_generated_at + timedelta(days=365) if assessment.certificate_generated_at else None
        writer.writerow([
            assessment.certificate_id,
            assessment.organization_name,
            assessment.ai_system_name,
            f"{assessment.final_score:.1f}%" if assessment.final_score else '',
            assessment.risk_level,
            assessment.industry,
            assessment.certificate_generated_at.strftime('%Y-%m-%d') if assessment.certificate_generated_at else '',
            valid_until.strftime('%Y-%m-%d') if valid_until else '',
            'Valid'
        ])
    
    output.seek(0)
    return output.getvalue()

