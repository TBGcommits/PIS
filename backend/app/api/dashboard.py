from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.user import User
from app.models.tenant import Tenant
from app.models.project import Project, Task
from app.models.audit import FieldOperation
from sqlalchemy import func, and_
from datetime import datetime, timedelta

bp = Blueprint('dashboard', __name__)

@bp.before_request
@jwt_required()
def before_request():
    """Load tenant and user for all dashboard endpoints"""
    tenant_slug = request.headers.get('X-Tenant', 'default')
    tenant = Tenant.query.filter_by(slug=tenant_slug, is_active=True).first()
    if not tenant:
        return jsonify({'error': 'Invalid tenant'}), 400
    
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id, tenant_id=tenant.id, is_active=True).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    g.current_tenant = tenant
    g.current_user = user

@bp.route('/stats', methods=['GET'])
def get_dashboard_stats():
    """Get dashboard statistics"""
    tenant_id = g.current_tenant.id
    
    # Project statistics
    total_projects = Project.query.filter_by(tenant_id=tenant_id).count()
    active_projects = Project.query.filter_by(tenant_id=tenant_id, status='active').count()
    completed_projects = Project.query.filter_by(tenant_id=tenant_id, status='completed').count()
    
    # Task statistics
    total_tasks = Task.query.join(Project).filter(Project.tenant_id == tenant_id).count()
    completed_tasks = Task.query.join(Project).filter(
        and_(Project.tenant_id == tenant_id, Task.status == 'completed')
    ).count()
    in_progress_tasks = Task.query.join(Project).filter(
        and_(Project.tenant_id == tenant_id, Task.status == 'in_progress')
    ).count()
    
    # User statistics
    total_users = User.query.filter_by(tenant_id=tenant_id, is_active=True).count()
    
    # Recent activity (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_projects = Project.query.filter(
        and_(Project.tenant_id == tenant_id, Project.created_at >= week_ago)
    ).count()
    
    recent_tasks = Task.query.join(Project).filter(
        and_(Project.tenant_id == tenant_id, Task.created_at >= week_ago)
    ).count()
    
    # Field operations today
    today = datetime.utcnow().date()
    todays_operations = FieldOperation.query.filter(
        and_(
            FieldOperation.tenant_id == tenant_id,
            FieldOperation.operation_date == today
        )
    ).count()
    
    return jsonify({
        'projects': {
            'total': total_projects,
            'active': active_projects,
            'completed': completed_projects,
            'recent': recent_projects
        },
        'tasks': {
            'total': total_tasks,
            'completed': completed_tasks,
            'in_progress': in_progress_tasks,
            'recent': recent_tasks
        },
        'users': {
            'total': total_users
        },
        'field_operations': {
            'today': todays_operations
        }
    }), 200

@bp.route('/recent-activity', methods=['GET'])
def get_recent_activity():
    """Get recent activity for dashboard"""
    tenant_id = g.current_tenant.id
    limit = request.args.get('limit', 10, type=int)
    
    # Recent projects
    recent_projects = Project.query.filter_by(tenant_id=tenant_id)\
        .order_by(Project.created_at.desc())\
        .limit(limit).all()
    
    # Recent tasks
    recent_tasks = Task.query.join(Project)\
        .filter(Project.tenant_id == tenant_id)\
        .order_by(Task.created_at.desc())\
        .limit(limit).all()
    
    # Recent field operations
    recent_operations = FieldOperation.query.filter_by(tenant_id=tenant_id)\
        .order_by(FieldOperation.created_at.desc())\
        .limit(limit).all()
    
    return jsonify({
        'recent_projects': [project.to_dict() for project in recent_projects],
        'recent_tasks': [task.to_dict() for task in recent_tasks],
        'recent_operations': [op.to_dict() for op in recent_operations]
    }), 200

@bp.route('/my-tasks', methods=['GET'])
def get_my_tasks():
    """Get tasks assigned to current user"""
    status_filter = request.args.get('status')
    limit = request.args.get('limit', 20, type=int)
    
    query = Task.query.join(Project).filter(
        and_(
            Project.tenant_id == g.current_tenant.id,
            Task.assigned_to == g.current_user.id
        )
    )
    
    if status_filter:
        query = query.filter(Task.status == status_filter)
    
    tasks = query.order_by(Task.due_date.asc().nullslast(), Task.created_at.desc())\
        .limit(limit).all()
    
    return jsonify({
        'tasks': [task.to_dict() for task in tasks]
    }), 200

@bp.route('/project-progress', methods=['GET'])
def get_project_progress():
    """Get project progress summary"""
    projects = Project.query.filter_by(tenant_id=g.current_tenant.id).all()
    
    progress_data = []
    for project in projects:
        progress_data.append({
            'project': project.to_dict(),
            'progress_percentage': project.progress_percentage,
            'task_counts': {
                'total': len(project.tasks),
                'completed': sum(1 for task in project.tasks if task.status == 'completed'),
                'in_progress': sum(1 for task in project.tasks if task.status == 'in_progress'),
                'not_started': sum(1 for task in project.tasks if task.status == 'not_started')
            }
        })
    
    return jsonify({
        'project_progress': progress_data
    }), 200

@bp.route('/notifications', methods=['GET'])
def get_notifications():
    """Get user notifications (placeholder for future implementation)"""
    # This is a placeholder for future notification system
    notifications = []
    
    # Add some sample notifications based on current data
    user_tasks = Task.query.join(Project).filter(
        and_(
            Project.tenant_id == g.current_tenant.id,
            Task.assigned_to == g.current_user.id,
            Task.status != 'completed'
        )
    ).all()
    
    # Overdue tasks
    now = datetime.utcnow()
    for task in user_tasks:
        if task.due_date and task.due_date < now:
            notifications.append({
                'id': f'task_overdue_{task.id}',
                'type': 'warning',
                'title': 'Overdue Task',
                'message': f'Task "{task.title}" is overdue',
                'created_at': task.due_date.isoformat(),
                'link': f'/projects/{task.project_id}/tasks/{task.id}'
            })
    
    # Tasks due soon (next 24 hours)
    tomorrow = now + timedelta(days=1)
    for task in user_tasks:
        if task.due_date and now < task.due_date <= tomorrow:
            notifications.append({
                'id': f'task_due_soon_{task.id}',
                'type': 'info',
                'title': 'Task Due Soon',
                'message': f'Task "{task.title}" is due soon',
                'created_at': task.due_date.isoformat(),
                'link': f'/projects/{task.project_id}/tasks/{task.id}'
            })
    
    # Sort by date
    notifications.sort(key=lambda x: x['created_at'], reverse=True)
    
    return jsonify({
        'notifications': notifications[:20]  # Limit to 20 most recent
    }), 200