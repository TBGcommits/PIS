from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate
try:
    from flask_babel import Babel
except ImportError:
    Babel = None
from config import Config

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()
babel = Babel() if Babel else None

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions with app
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    if babel:
        babel.init_app(app)
    CORS(app)
    
    # Import models to ensure they are registered with SQLAlchemy
    from app.models import user, tenant, project, audit, rbac
    
    # Register blueprints
    from app.api import auth, projects, dashboard, field_ops
    app.register_blueprint(auth.bp, url_prefix='/api/auth')
    app.register_blueprint(projects.bp, url_prefix='/api/projects')
    app.register_blueprint(dashboard.bp, url_prefix='/api/dashboard')
    app.register_blueprint(field_ops.bp, url_prefix='/api/field-ops')
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Create default tenant if not exists
        from app.models.tenant import Tenant
        if not Tenant.query.filter_by(slug='default').first():
            default_tenant = Tenant(
                name='Default Tenant',
                slug='default',
                is_active=True
            )
            db.session.add(default_tenant)
            db.session.commit()
    
    return app