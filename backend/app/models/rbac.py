from app import db
from datetime import datetime
import uuid

class Role(db.Model):
    """RBAC Role model"""
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_system = db.Column(db.Boolean, default=False)  # System roles cannot be deleted
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'name', name='unique_role_per_tenant'),
    )
    
    # Relationships
    permissions = db.relationship('RolePermission', backref='role', lazy=True, cascade='all, delete-orphan')
    user_roles = db.relationship('UserRole', backref='role', lazy=True)
    
    def has_permission(self, permission_name):
        """Check if role has specific permission"""
        return any(rp.permission.name == permission_name and rp.is_active 
                  for rp in self.permissions if rp.permission.is_active)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_system': self.is_system,
            'is_active': self.is_active,
            'permissions': [rp.permission.name for rp in self.permissions if rp.is_active]
        }

class Permission(db.Model):
    """RBAC Permission model"""
    __tablename__ = 'permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # e.g., 'projects', 'users', 'reports'
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    role_permissions = db.relationship('RolePermission', backref='permission', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'is_active': self.is_active
        }

class UserRole(db.Model):
    """Many-to-many relationship between Users and Roles"""
    __tablename__ = 'user_roles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    assigned_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'role_id', name='unique_user_role'),
    )

class RolePermission(db.Model):
    """Many-to-many relationship between Roles and Permissions"""
    __tablename__ = 'role_permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    permission_id = db.Column(db.Integer, db.ForeignKey('permissions.id'), nullable=False)
    granted_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    granted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    __table_args__ = (
        db.UniqueConstraint('role_id', 'permission_id', name='unique_role_permission'),
    )