from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db
from app.models.user import User
from app.models.tenant import Tenant
from app.models.audit import AuditLog
from datetime import datetime

bp = Blueprint('auth', __name__)

@bp.before_request
def load_tenant():
    """Load tenant from request headers"""
    tenant_slug = request.headers.get('X-Tenant', 'default')
    tenant = Tenant.query.filter_by(slug=tenant_slug, is_active=True).first()
    if not tenant:
        return jsonify({'error': 'Invalid tenant'}), 400
    g.current_tenant = tenant

@bp.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required'}), 400
    
    # Find user in current tenant
    user = User.query.filter_by(
        username=data['username'],
        tenant_id=g.current_tenant.id,
        is_active=True
    ).first()
    
    if not user or not user.check_password(data['password']):
        # Log failed login attempt
        AuditLog.log_action(
            action='LOGIN_FAILED',
            resource_type='User',
            description=f'Failed login attempt for username: {data["username"]}',
            tenant_id=g.current_tenant.id
        )
        db.session.commit()
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Update last login
    user.last_login = datetime.utcnow()
    
    # Create access token
    access_token = create_access_token(identity=user.id)
    
    # Log successful login
    AuditLog.log_action(
        action='LOGIN_SUCCESS',
        resource_type='User',
        resource_id=user.id,
        user_id=user.id,
        description='User logged in successfully',
        tenant_id=g.current_tenant.id
    )
    
    db.session.commit()
    
    return jsonify({
        'access_token': access_token,
        'user': user.to_dict(),
        'tenant': g.current_tenant.to_dict()
    }), 200

@bp.route('/register', methods=['POST'])
def register():
    """User registration endpoint"""
    data = request.get_json()
    
    required_fields = ['username', 'email', 'password', 'first_name', 'last_name']
    if not data or not all(field in data for field in required_fields):
        return jsonify({'error': 'All fields are required'}), 400
    
    # Check if user already exists in tenant
    existing_user = User.query.filter(
        (User.username == data['username']) | (User.email == data['email']),
        User.tenant_id == g.current_tenant.id
    ).first()
    
    if existing_user:
        return jsonify({'error': 'Username or email already exists'}), 409
    
    # Create new user
    user = User(
        tenant_id=g.current_tenant.id,
        username=data['username'],
        email=data['email'],
        first_name=data['first_name'],
        last_name=data['last_name'],
        phone=data.get('phone'),
        language=data.get('language', 'en')
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.flush()  # To get the user ID
    
    # Log user creation
    AuditLog.log_action(
        action='CREATE',
        resource_type='User',
        resource_id=user.id,
        new_values=user.to_dict(),
        description='New user registered',
        tenant_id=g.current_tenant.id
    )
    
    db.session.commit()
    
    return jsonify({
        'message': 'User registered successfully',
        'user': user.to_dict()
    }), 201

@bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id, tenant_id=g.current_tenant.id).first()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': user.to_dict()}), 200

@bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update current user profile"""
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id, tenant_id=g.current_tenant.id).first()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Store old values for audit
    old_values = user.to_dict()
    
    # Update allowed fields
    allowed_fields = ['first_name', 'last_name', 'phone', 'language', 'timezone']
    for field in allowed_fields:
        if field in data:
            setattr(user, field, data[field])
    
    # Log profile update
    AuditLog.log_action(
        action='UPDATE',
        resource_type='User',
        resource_id=user.id,
        user_id=user.id,
        old_values=old_values,
        new_values=user.to_dict(),
        description='User profile updated',
        tenant_id=g.current_tenant.id
    )
    
    db.session.commit()
    
    return jsonify({
        'message': 'Profile updated successfully',
        'user': user.to_dict()
    }), 200

@bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id, tenant_id=g.current_tenant.id).first()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    if not data or not data.get('current_password') or not data.get('new_password'):
        return jsonify({'error': 'Current password and new password are required'}), 400
    
    # Verify current password
    if not user.check_password(data['current_password']):
        return jsonify({'error': 'Current password is incorrect'}), 400
    
    # Update password
    user.set_password(data['new_password'])
    
    # Log password change
    AuditLog.log_action(
        action='PASSWORD_CHANGE',
        resource_type='User',
        resource_id=user.id,
        user_id=user.id,
        description='User changed password',
        tenant_id=g.current_tenant.id
    )
    
    db.session.commit()
    
    return jsonify({'message': 'Password changed successfully'}), 200