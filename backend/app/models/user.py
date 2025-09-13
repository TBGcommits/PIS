from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

class User(db.Model):
    """User model with multi-tenant support"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    
    # Basic user information
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Personal information
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    
    # User preferences
    language = db.Column(db.String(5), default='en')  # en, ar, es
    timezone = db.Column(db.String(50), default='UTC')
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    last_login = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Unique constraint per tenant
    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'username', name='unique_username_per_tenant'),
        db.UniqueConstraint('tenant_id', 'email', name='unique_email_per_tenant'),
    )
    
    # Relationships
    user_roles = db.relationship('UserRole', backref='user', lazy=True, cascade='all, delete-orphan', foreign_keys='UserRole.user_id')
    audit_logs = db.relationship('AuditLog', backref='user', lazy=True, foreign_keys='AuditLog.user_id')
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def get_roles(self):
        """Get user roles for current tenant"""
        return [ur.role for ur in self.user_roles if ur.is_active]
    
    def has_permission(self, permission):
        """Check if user has specific permission"""
        for role in self.get_roles():
            if role.has_permission(permission):
                return True
        return False
    
    @property
    def full_name(self):
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'tenant_id': self.tenant_id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'phone': self.phone,
            'language': self.language,
            'timezone': self.timezone,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'roles': [role.name for role in self.get_roles()]
        }