from app import db
from datetime import datetime
import uuid

class Project(db.Model):
    """Project model for construction project management"""
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    
    # Basic project information
    name = db.Column(db.String(255), nullable=False)
    code = db.Column(db.String(50))  # Project code/number
    description = db.Column(db.Text)
    
    # Project status
    status = db.Column(db.String(50), default='planning')  # planning, active, paused, completed, cancelled
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    
    # Dates
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    actual_start_date = db.Column(db.Date)
    actual_end_date = db.Column(db.Date)
    
    # Financial
    budget = db.Column(db.Float, default=0.0)
    cost_to_date = db.Column(db.Float, default=0.0)
    
    # Location
    location = db.Column(db.String(255))
    coordinates = db.Column(db.String(100))  # latitude,longitude
    
    # Project manager
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Unique constraint per tenant
    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'code', name='unique_project_code_per_tenant'),
    )
    
    # Relationships
    manager = db.relationship('User', backref='managed_projects', foreign_keys=[manager_id])
    tasks = db.relationship('Task', backref='project', lazy=True, cascade='all, delete-orphan')
    modules = db.relationship('ProjectModule', backref='project', lazy=True, cascade='all, delete-orphan')
    teams = db.relationship('ProjectTeam', backref='project', lazy=True, cascade='all, delete-orphan')
    
    @property
    def progress_percentage(self):
        """Calculate project progress based on completed tasks"""
        if not self.tasks:
            return 0
        completed_tasks = sum(1 for task in self.tasks if task.status == 'completed')
        return (completed_tasks / len(self.tasks)) * 100 if self.tasks else 0
    
    def to_dict(self):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'tenant_id': self.tenant_id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'actual_start_date': self.actual_start_date.isoformat() if self.actual_start_date else None,
            'actual_end_date': self.actual_end_date.isoformat() if self.actual_end_date else None,
            'budget': self.budget,
            'cost_to_date': self.cost_to_date,
            'location': self.location,
            'coordinates': self.coordinates,
            'manager_id': self.manager_id,
            'manager_name': self.manager.full_name if self.manager else None,
            'progress_percentage': self.progress_percentage,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ProjectModule(db.Model):
    """Hierarchical project modules"""
    __tablename__ = 'project_modules'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('project_modules.id'))
    
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    order = db.Column(db.Integer, default=0)
    
    # Status
    status = db.Column(db.String(50), default='not_started')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Self-referential relationship for hierarchy
    children = db.relationship('ProjectModule', backref=db.backref('parent', remote_side=[id]))
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'parent_id': self.parent_id,
            'name': self.name,
            'description': self.description,
            'order': self.order,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Task(db.Model):
    """Task model for project tasks"""
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('project_modules.id'))
    
    # Task information
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='not_started')  # not_started, in_progress, completed, blocked
    priority = db.Column(db.String(20), default='medium')
    
    # Assignment
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    assigned_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Dates
    due_date = db.Column(db.DateTime)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    module = db.relationship('ProjectModule', backref='tasks')
    assignee = db.relationship('User', foreign_keys=[assigned_to], backref='assigned_tasks')
    assigner = db.relationship('User', foreign_keys=[assigned_by])
    
    def to_dict(self):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'project_id': self.project_id,
            'module_id': self.module_id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'assigned_to': self.assigned_to,
            'assigned_by': self.assigned_by,
            'assignee_name': self.assignee.full_name if self.assignee else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ProjectTeam(db.Model):
    """Project team members"""
    __tablename__ = 'project_teams'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(100))  # e.g., 'supervisor', 'engineer', 'worker'
    joined_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    __table_args__ = (
        db.UniqueConstraint('project_id', 'user_id', name='unique_project_team_member'),
    )
    
    # Relationships
    user = db.relationship('User', backref='project_memberships')
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else None,
            'role': self.role,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
            'is_active': self.is_active
        }