from app import db
from datetime import datetime
import uuid

class Tenant(db.Model):
    """Multi-tenant support - each tenant has isolated data"""
    __tablename__ = 'tenants'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Configuration settings for tenant
    settings = db.Column(db.JSON, default={})
    
    # Relationships
    users = db.relationship('User', backref='tenant', lazy=True)
    projects = db.relationship('Project', backref='tenant', lazy=True)
    
    def __repr__(self):
        return f'<Tenant {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'settings': self.settings
        }