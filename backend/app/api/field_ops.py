from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.user import User
from app.models.tenant import Tenant
from app.models.project import Project
from app.models.audit import FieldOperation, AuditLog
from datetime import datetime, time

bp = Blueprint('field_ops', __name__)

@bp.before_request
@jwt_required()
def before_request():
    """Load tenant and user for all field operations endpoints"""
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

@bp.route('/daily-log', methods=['POST'])
def create_daily_log():
    """Create daily work log entry"""
    data = request.get_json()
    
    if not data or not data.get('project_id') or not data.get('title'):
        return jsonify({'error': 'Project ID and title are required'}), 400
    
    # Verify project exists and user has access
    project = Project.query.filter_by(
        id=data['project_id'],
        tenant_id=g.current_tenant.id
    ).first()
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    # Create field operation entry
    field_op = FieldOperation(
        tenant_id=g.current_tenant.id,
        project_id=data['project_id'],
        operation_type='daily_log',
        title=data['title'],
        description=data.get('description'),
        user_id=g.current_user.id,
        team_id=data.get('team_id'),
        location=data.get('location'),
        coordinates=data.get('coordinates'),
        operation_date=datetime.fromisoformat(data['operation_date']).date() if data.get('operation_date') else datetime.utcnow().date(),
        start_time=datetime.fromisoformat(data['start_time']).time() if data.get('start_time') else None,
        end_time=datetime.fromisoformat(data['end_time']).time() if data.get('end_time') else None,
        data={
            'work_completed': data.get('work_completed'),
            'materials_used': data.get('materials_used'),
            'equipment_used': data.get('equipment_used'),
            'weather_conditions': data.get('weather_conditions'),
            'issues_encountered': data.get('issues_encountered'),
            'photos': data.get('photos', [])
        }
    )
    
    db.session.add(field_op)
    db.session.flush()
    
    # Log the action
    AuditLog.log_action(
        action='CREATE',
        resource_type='FieldOperation',
        resource_id=field_op.id,
        new_values=field_op.to_dict(),
        description=f'Daily log created for project "{project.name}"',
        tenant_id=g.current_tenant.id
    )
    
    db.session.commit()
    
    return jsonify({
        'message': 'Daily log created successfully',
        'field_operation': field_op.to_dict()
    }), 201

@bp.route('/attendance', methods=['POST'])
def record_attendance():
    """Record worker attendance"""
    data = request.get_json()
    
    if not data or not data.get('project_id') or not data.get('attendance_type'):
        return jsonify({'error': 'Project ID and attendance type are required'}), 400
    
    if data['attendance_type'] not in ['check_in', 'check_out']:
        return jsonify({'error': 'Invalid attendance type'}), 400
    
    # Verify project exists
    project = Project.query.filter_by(
        id=data['project_id'],
        tenant_id=g.current_tenant.id
    ).first()
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    current_time = datetime.utcnow()
    
    # Create attendance record
    field_op = FieldOperation(
        tenant_id=g.current_tenant.id,
        project_id=data['project_id'],
        operation_type='attendance',
        title=f"Attendance - {data['attendance_type'].replace('_', ' ').title()}",
        description=data.get('notes'),
        user_id=g.current_user.id,
        location=data.get('location'),
        coordinates=data.get('coordinates'),
        operation_date=current_time.date(),
        start_time=current_time.time() if data['attendance_type'] == 'check_in' else None,
        end_time=current_time.time() if data['attendance_type'] == 'check_out' else None,
        data={
            'attendance_type': data['attendance_type'],
            'timestamp': current_time.isoformat(),
            'notes': data.get('notes')
        }
    )
    
    db.session.add(field_op)
    db.session.flush()
    
    # Log the action
    AuditLog.log_action(
        action='CREATE',
        resource_type='FieldOperation',
        resource_id=field_op.id,
        new_values=field_op.to_dict(),
        description=f'Attendance {data["attendance_type"]} recorded for project "{project.name}"',
        tenant_id=g.current_tenant.id
    )
    
    db.session.commit()
    
    return jsonify({
        'message': 'Attendance recorded successfully',
        'field_operation': field_op.to_dict()
    }), 201

@bp.route('/material-request', methods=['POST'])
def create_material_request():
    """Create material request"""
    data = request.get_json()
    
    if not data or not data.get('project_id') or not data.get('materials'):
        return jsonify({'error': 'Project ID and materials list are required'}), 400
    
    # Verify project exists
    project = Project.query.filter_by(
        id=data['project_id'],
        tenant_id=g.current_tenant.id
    ).first()
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    # Create material request
    field_op = FieldOperation(
        tenant_id=g.current_tenant.id,
        project_id=data['project_id'],
        operation_type='material_request',
        title=data.get('title', 'Material Request'),
        description=data.get('description'),
        user_id=g.current_user.id,
        location=data.get('location'),
        operation_date=datetime.utcnow().date(),
        status='pending',
        data={
            'materials': data['materials'],  # List of materials with quantities
            'urgency': data.get('urgency', 'normal'),
            'needed_by': data.get('needed_by'),
            'justification': data.get('justification')
        }
    )
    
    db.session.add(field_op)
    db.session.flush()
    
    # Log the action
    AuditLog.log_action(
        action='CREATE',
        resource_type='FieldOperation',
        resource_id=field_op.id,
        new_values=field_op.to_dict(),
        description=f'Material request created for project "{project.name}"',
        tenant_id=g.current_tenant.id
    )
    
    db.session.commit()
    
    return jsonify({
        'message': 'Material request created successfully',
        'field_operation': field_op.to_dict()
    }), 201

@bp.route('/operations', methods=['GET'])
def list_field_operations():
    """List field operations with filtering"""
    project_id = request.args.get('project_id', type=int)
    operation_type = request.args.get('operation_type')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    status = request.args.get('status')
    limit = request.args.get('limit', 50, type=int)
    
    query = FieldOperation.query.filter_by(tenant_id=g.current_tenant.id)
    
    if project_id:
        query = query.filter_by(project_id=project_id)
    
    if operation_type:
        query = query.filter_by(operation_type=operation_type)
    
    if status:
        query = query.filter_by(status=status)
    
    if date_from:
        query = query.filter(FieldOperation.operation_date >= datetime.fromisoformat(date_from).date())
    
    if date_to:
        query = query.filter(FieldOperation.operation_date <= datetime.fromisoformat(date_to).date())
    
    operations = query.order_by(FieldOperation.created_at.desc()).limit(limit).all()
    
    return jsonify({
        'field_operations': [op.to_dict() for op in operations]
    }), 200

@bp.route('/operations/<int:operation_id>', methods=['GET'])
def get_field_operation(operation_id):
    """Get specific field operation"""
    operation = FieldOperation.query.filter_by(
        id=operation_id,
        tenant_id=g.current_tenant.id
    ).first()
    
    if not operation:
        return jsonify({'error': 'Field operation not found'}), 404
    
    return jsonify({
        'field_operation': operation.to_dict()
    }), 200

@bp.route('/operations/<int:operation_id>/approve', methods=['POST'])
def approve_field_operation(operation_id):
    """Approve or reject field operation"""
    operation = FieldOperation.query.filter_by(
        id=operation_id,
        tenant_id=g.current_tenant.id
    ).first()
    
    if not operation:
        return jsonify({'error': 'Field operation not found'}), 404
    
    data = request.get_json()
    action = data.get('action')  # 'approve' or 'reject'
    
    if action not in ['approve', 'reject']:
        return jsonify({'error': 'Invalid action'}), 400
    
    # Store old values for audit
    old_values = operation.to_dict()
    
    # Update operation status
    operation.status = 'approved' if action == 'approve' else 'rejected'
    operation.approved_by = g.current_user.id
    operation.approved_at = datetime.utcnow()
    
    # Add approval notes to data
    if not operation.data:
        operation.data = {}
    operation.data['approval_notes'] = data.get('notes')
    
    # Log the action
    AuditLog.log_action(
        action='UPDATE',
        resource_type='FieldOperation',
        resource_id=operation.id,
        old_values=old_values,
        new_values=operation.to_dict(),
        description=f'Field operation {action}d',
        tenant_id=g.current_tenant.id
    )
    
    db.session.commit()
    
    return jsonify({
        'message': f'Field operation {action}d successfully',
        'field_operation': operation.to_dict()
    }), 200

@bp.route('/dashboard', methods=['GET'])
def field_ops_dashboard():
    """Get field operations dashboard data"""
    tenant_id = g.current_tenant.id
    today = datetime.utcnow().date()
    
    # Today's operations
    todays_ops = FieldOperation.query.filter_by(
        tenant_id=tenant_id,
        operation_date=today
    ).all()
    
    # Pending approvals
    pending_ops = FieldOperation.query.filter_by(
        tenant_id=tenant_id,
        status='pending'
    ).count()
    
    # Operations by type today
    ops_by_type = {}
    for op in todays_ops:
        ops_by_type[op.operation_type] = ops_by_type.get(op.operation_type, 0) + 1
    
    # Active workers (users who checked in today)
    active_workers = FieldOperation.query.filter_by(
        tenant_id=tenant_id,
        operation_type='attendance',
        operation_date=today
    ).filter(
        FieldOperation.data['attendance_type'].astext == 'check_in'
    ).count()
    
    return jsonify({
        'todays_operations': {
            'total': len(todays_ops),
            'by_type': ops_by_type
        },
        'pending_approvals': pending_ops,
        'active_workers': active_workers,
        'recent_operations': [op.to_dict() for op in todays_ops[-10:]]  # Last 10
    }), 200