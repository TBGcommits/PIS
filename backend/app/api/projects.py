from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.user import User
from app.models.tenant import Tenant
from app.models.project import Project, Task, ProjectModule, ProjectTeam
from app.models.audit import AuditLog
from datetime import datetime
from sqlalchemy import and_

bp = Blueprint('projects', __name__)

@bp.before_request
@jwt_required()
def before_request():
    """Load tenant and user for all project endpoints"""
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

@bp.route('/', methods=['GET'])
def list_projects():
    """List all projects for current tenant"""
    projects = Project.query.filter_by(tenant_id=g.current_tenant.id).all()
    return jsonify({
        'projects': [project.to_dict() for project in projects]
    }), 200

@bp.route('/', methods=['POST'])
def create_project():
    """Create a new project"""
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({'error': 'Project name is required'}), 400
    
    # Check if project code exists
    if data.get('code'):
        existing = Project.query.filter_by(
            tenant_id=g.current_tenant.id,
            code=data['code']
        ).first()
        if existing:
            return jsonify({'error': 'Project code already exists'}), 409
    
    project = Project(
        tenant_id=g.current_tenant.id,
        name=data['name'],
        code=data.get('code'),
        description=data.get('description'),
        status=data.get('status', 'planning'),
        priority=data.get('priority', 'medium'),
        start_date=datetime.fromisoformat(data['start_date']).date() if data.get('start_date') else None,
        end_date=datetime.fromisoformat(data['end_date']).date() if data.get('end_date') else None,
        budget=data.get('budget', 0.0),
        location=data.get('location'),
        coordinates=data.get('coordinates'),
        manager_id=data.get('manager_id')
    )
    
    db.session.add(project)
    db.session.flush()
    
    # Log project creation
    AuditLog.log_action(
        action='CREATE',
        resource_type='Project',
        resource_id=project.id,
        new_values=project.to_dict(),
        description=f'Project "{project.name}" created',
        tenant_id=g.current_tenant.id
    )
    
    db.session.commit()
    
    return jsonify({
        'message': 'Project created successfully',
        'project': project.to_dict()
    }), 201

@bp.route('/<int:project_id>', methods=['GET'])
def get_project(project_id):
    """Get project details"""
    project = Project.query.filter_by(
        id=project_id,
        tenant_id=g.current_tenant.id
    ).first()
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    return jsonify({'project': project.to_dict()}), 200

@bp.route('/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    """Update project"""
    project = Project.query.filter_by(
        id=project_id,
        tenant_id=g.current_tenant.id
    ).first()
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Store old values for audit
    old_values = project.to_dict()
    
    # Update allowed fields
    allowed_fields = ['name', 'description', 'status', 'priority', 'budget', 
                     'location', 'coordinates', 'manager_id']
    for field in allowed_fields:
        if field in data:
            setattr(project, field, data[field])
    
    # Handle date fields
    if 'start_date' in data and data['start_date']:
        project.start_date = datetime.fromisoformat(data['start_date']).date()
    if 'end_date' in data and data['end_date']:
        project.end_date = datetime.fromisoformat(data['end_date']).date()
    
    # Log project update
    AuditLog.log_action(
        action='UPDATE',
        resource_type='Project',
        resource_id=project.id,
        old_values=old_values,
        new_values=project.to_dict(),
        description=f'Project "{project.name}" updated',
        tenant_id=g.current_tenant.id
    )
    
    db.session.commit()
    
    return jsonify({
        'message': 'Project updated successfully',
        'project': project.to_dict()
    }), 200

@bp.route('/<int:project_id>/tasks', methods=['GET'])
def list_project_tasks(project_id):
    """List tasks for a project"""
    project = Project.query.filter_by(
        id=project_id,
        tenant_id=g.current_tenant.id
    ).first()
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    tasks = Task.query.filter_by(project_id=project_id).all()
    return jsonify({
        'tasks': [task.to_dict() for task in tasks]
    }), 200

@bp.route('/<int:project_id>/tasks', methods=['POST'])
def create_task(project_id):
    """Create a new task for a project"""
    project = Project.query.filter_by(
        id=project_id,
        tenant_id=g.current_tenant.id
    ).first()
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    data = request.get_json()
    if not data or not data.get('title'):
        return jsonify({'error': 'Task title is required'}), 400
    
    task = Task(
        project_id=project_id,
        module_id=data.get('module_id'),
        title=data['title'],
        description=data.get('description'),
        status=data.get('status', 'not_started'),
        priority=data.get('priority', 'medium'),
        assigned_to=data.get('assigned_to'),
        assigned_by=g.current_user.id,
        due_date=datetime.fromisoformat(data['due_date']) if data.get('due_date') else None
    )
    
    db.session.add(task)
    db.session.flush()
    
    # Log task creation
    AuditLog.log_action(
        action='CREATE',
        resource_type='Task',
        resource_id=task.id,
        new_values=task.to_dict(),
        description=f'Task "{task.title}" created in project "{project.name}"',
        tenant_id=g.current_tenant.id
    )
    
    db.session.commit()
    
    return jsonify({
        'message': 'Task created successfully',
        'task': task.to_dict()
    }), 201

@bp.route('/<int:project_id>/modules', methods=['GET'])
def list_project_modules(project_id):
    """List modules for a project"""
    project = Project.query.filter_by(
        id=project_id,
        tenant_id=g.current_tenant.id
    ).first()
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    modules = ProjectModule.query.filter_by(project_id=project_id).all()
    return jsonify({
        'modules': [module.to_dict() for module in modules]
    }), 200

@bp.route('/<int:project_id>/modules', methods=['POST'])
def create_module(project_id):
    """Create a new module for a project"""
    project = Project.query.filter_by(
        id=project_id,
        tenant_id=g.current_tenant.id
    ).first()
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'error': 'Module name is required'}), 400
    
    module = ProjectModule(
        project_id=project_id,
        parent_id=data.get('parent_id'),
        name=data['name'],
        description=data.get('description'),
        order=data.get('order', 0)
    )
    
    db.session.add(module)
    db.session.flush()
    
    # Log module creation
    AuditLog.log_action(
        action='CREATE',
        resource_type='ProjectModule',
        resource_id=module.id,
        new_values=module.to_dict(),
        description=f'Module "{module.name}" created in project "{project.name}"',
        tenant_id=g.current_tenant.id
    )
    
    db.session.commit()
    
    return jsonify({
        'message': 'Module created successfully',
        'module': module.to_dict()
    }), 201

@bp.route('/<int:project_id>/team', methods=['GET'])
def list_project_team(project_id):
    """List team members for a project"""
    project = Project.query.filter_by(
        id=project_id,
        tenant_id=g.current_tenant.id
    ).first()
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    team_members = ProjectTeam.query.filter_by(
        project_id=project_id,
        is_active=True
    ).all()
    
    return jsonify({
        'team_members': [member.to_dict() for member in team_members]
    }), 200

@bp.route('/<int:project_id>/team', methods=['POST'])
def add_team_member(project_id):
    """Add team member to project"""
    project = Project.query.filter_by(
        id=project_id,
        tenant_id=g.current_tenant.id
    ).first()
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    data = request.get_json()
    if not data or not data.get('user_id'):
        return jsonify({'error': 'User ID is required'}), 400
    
    # Check if user exists in same tenant
    user = User.query.filter_by(
        id=data['user_id'],
        tenant_id=g.current_tenant.id,
        is_active=True
    ).first()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if already a team member
    existing = ProjectTeam.query.filter_by(
        project_id=project_id,
        user_id=data['user_id']
    ).first()
    
    if existing:
        if existing.is_active:
            return jsonify({'error': 'User is already a team member'}), 409
        else:
            # Reactivate existing membership
            existing.is_active = True
            existing.role = data.get('role', 'member')
            member = existing
    else:
        # Create new team membership
        member = ProjectTeam(
            project_id=project_id,
            user_id=data['user_id'],
            role=data.get('role', 'member')
        )
        db.session.add(member)
    
    db.session.flush()
    
    # Log team member addition
    AuditLog.log_action(
        action='CREATE',
        resource_type='ProjectTeam',
        resource_id=member.id,
        new_values=member.to_dict(),
        description=f'User "{user.full_name}" added to project "{project.name}" team',
        tenant_id=g.current_tenant.id
    )
    
    db.session.commit()
    
    return jsonify({
        'message': 'Team member added successfully',
        'team_member': member.to_dict()
    }), 201