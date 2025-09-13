from app import db
from datetime import datetime
import uuid
import json

class AuditLog(db.Model):
    """Immutable audit trail for all system actions"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    
    # Action details
    action = db.Column(db.String(100), nullable=False)  # CREATE, UPDATE, DELETE, LOGIN, etc.
    resource_type = db.Column(db.String(100), nullable=False)  # User, Project, Task, etc.
    resource_id = db.Column(db.String(100))  # ID of the affected resource
    
    # User who performed the action
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user_ip = db.Column(db.String(45))  # IPv4 or IPv6
    user_agent = db.Column(db.Text)
    
    # Changes made
    old_values = db.Column(db.JSON)  # Previous state of the resource
    new_values = db.Column(db.JSON)  # New state of the resource
    
    # Additional context
    description = db.Column(db.Text)
    extra_data = db.Column(db.JSON)  # Additional context data
    
    # Timestamp (immutable)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    tenant = db.relationship('Tenant', backref='audit_logs')
    
    def __repr__(self):
        return f'<AuditLog {self.action} on {self.resource_type}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'tenant_id': self.tenant_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else 'System',
            'user_ip': self.user_ip,
            'user_agent': self.user_agent,
            'old_values': self.old_values,
            'new_values': self.new_values,
            'description': self.description,
            'extra_data': self.extra_data,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @staticmethod
    def log_action(action, resource_type, resource_id=None, user_id=None, 
                   old_values=None, new_values=None, description=None, 
                   extra_data=None, user_ip=None, user_agent=None, tenant_id=None):
        """Static method to log an action to the audit trail"""
        from flask import g, request
        
        # Get tenant_id from current context if not provided
        if tenant_id is None and hasattr(g, 'current_tenant'):
            tenant_id = g.current_tenant.id
        
        # Get user info from current context if not provided
        if user_id is None and hasattr(g, 'current_user'):
            user_id = g.current_user.id
            
        if user_ip is None and request:
            user_ip = request.remote_addr
            
        if user_agent is None and request:
            user_agent = request.headers.get('User-Agent')
        
        audit_log = AuditLog(
            tenant_id=tenant_id,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            user_id=user_id,
            user_ip=user_ip,
            user_agent=user_agent,
            old_values=old_values,
            new_values=new_values,
            description=description,
            extra_data=extra_data
        )
        
        db.session.add(audit_log)
        # Note: commit should be handled by the calling function
        
        return audit_log

class FieldOperation(db.Model):
    """Field operations and daily activities tracking"""
    __tablename__ = 'field_operations'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    
    # Operation details
    operation_type = db.Column(db.String(100), nullable=False)  # daily_log, attendance, material_request
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    
    # Worker/team involved
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    team_id = db.Column(db.String(100))  # Team identifier
    
    # Location and time
    location = db.Column(db.String(255))
    coordinates = db.Column(db.String(100))  # latitude,longitude
    operation_date = db.Column(db.Date, default=datetime.utcnow().date, nullable=False)
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    
    # Status and approval
    status = db.Column(db.String(50), default='pending')  # pending, approved, rejected
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime)
    
    # Additional data
    data = db.Column(db.JSON)  # Flexible data storage for different operation types
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    tenant = db.relationship('Tenant', backref='field_operations')
    project = db.relationship('Project', backref='field_operations')
    user = db.relationship('User', foreign_keys=[user_id], backref='field_operations')
    approver = db.relationship('User', foreign_keys=[approved_by])
    
    def to_dict(self):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'tenant_id': self.tenant_id,
            'project_id': self.project_id,
            'project_name': self.project.name if self.project else None,
            'operation_type': self.operation_type,
            'title': self.title,
            'description': self.description,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else None,
            'team_id': self.team_id,
            'location': self.location,
            'coordinates': self.coordinates,
            'operation_date': self.operation_date.isoformat() if self.operation_date else None,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'data': self.data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }