from app import create_app, db
from app.models.user import User
from app.models.tenant import Tenant
from app.models.rbac import Role, Permission, UserRole, RolePermission

app = create_app()

@app.cli.command()
def init_db():
    """Initialize database with sample data"""
    # Create tables
    db.create_all()
    
    # Create default tenant if not exists
    default_tenant = Tenant.query.filter_by(slug='default').first()
    if not default_tenant:
        default_tenant = Tenant(
            name='Default Company',
            slug='default',
            description='Default tenant for the system',
            is_active=True
        )
        db.session.add(default_tenant)
        db.session.flush()
    
    # Create basic permissions
    permissions_data = [
        ('user.create', 'Create users', 'users'),
        ('user.read', 'Read users', 'users'),
        ('user.update', 'Update users', 'users'),
        ('user.delete', 'Delete users', 'users'),
        ('project.create', 'Create projects', 'projects'),
        ('project.read', 'Read projects', 'projects'),
        ('project.update', 'Update projects', 'projects'),
        ('project.delete', 'Delete projects', 'projects'),
        ('task.create', 'Create tasks', 'tasks'),
        ('task.read', 'Read tasks', 'tasks'),
        ('task.update', 'Update tasks', 'tasks'),
        ('task.delete', 'Delete tasks', 'tasks'),
        ('fieldops.create', 'Create field operations', 'field_operations'),
        ('fieldops.read', 'Read field operations', 'field_operations'),
        ('fieldops.approve', 'Approve field operations', 'field_operations'),
        ('dashboard.read', 'Access dashboard', 'dashboard'),
        ('reports.read', 'Access reports', 'reports'),
    ]
    
    for perm_name, perm_desc, perm_cat in permissions_data:
        if not Permission.query.filter_by(name=perm_name).first():
            permission = Permission(
                name=perm_name,
                description=perm_desc,
                category=perm_cat
            )
            db.session.add(permission)
    
    db.session.flush()
    
    # Create basic roles
    roles_data = [
        ('Admin', 'System Administrator', True),
        ('Project Manager', 'Project Manager', False),
        ('Supervisor', 'Field Supervisor', False),
        ('Worker', 'Field Worker', False),
    ]
    
    for role_name, role_desc, is_system in roles_data:
        if not Role.query.filter_by(tenant_id=default_tenant.id, name=role_name).first():
            role = Role(
                tenant_id=default_tenant.id,
                name=role_name,
                description=role_desc,
                is_system=is_system
            )
            db.session.add(role)
            db.session.flush()
            
            # Assign permissions to roles
            if role_name == 'Admin':
                # Admin gets all permissions
                all_permissions = Permission.query.all()
                for permission in all_permissions:
                    role_perm = RolePermission(
                        role_id=role.id,
                        permission_id=permission.id
                    )
                    db.session.add(role_perm)
            
            elif role_name == 'Project Manager':
                # Project Manager gets project and task permissions
                pm_perms = ['project.create', 'project.read', 'project.update', 
                           'task.create', 'task.read', 'task.update', 
                           'fieldops.read', 'fieldops.approve', 'dashboard.read', 'reports.read']
                for perm_name in pm_perms:
                    permission = Permission.query.filter_by(name=perm_name).first()
                    if permission:
                        role_perm = RolePermission(
                            role_id=role.id,
                            permission_id=permission.id
                        )
                        db.session.add(role_perm)
            
            elif role_name == 'Supervisor':
                # Supervisor gets field operations and task permissions
                sup_perms = ['project.read', 'task.read', 'task.update', 
                            'fieldops.create', 'fieldops.read', 'fieldops.approve', 'dashboard.read']
                for perm_name in sup_perms:
                    permission = Permission.query.filter_by(name=perm_name).first()
                    if permission:
                        role_perm = RolePermission(
                            role_id=role.id,
                            permission_id=permission.id
                        )
                        db.session.add(role_perm)
            
            elif role_name == 'Worker':
                # Worker gets basic read and field operations
                worker_perms = ['project.read', 'task.read', 'fieldops.create', 'fieldops.read', 'dashboard.read']
                for perm_name in worker_perms:
                    permission = Permission.query.filter_by(name=perm_name).first()
                    if permission:
                        role_perm = RolePermission(
                            role_id=role.id,
                            permission_id=permission.id
                        )
                        db.session.add(role_perm)
    
    # Create default admin user
    admin_user = User.query.filter_by(tenant_id=default_tenant.id, username='admin').first()
    if not admin_user:
        admin_user = User(
            tenant_id=default_tenant.id,
            username='admin',
            email='admin@tbg-pis.com',
            first_name='System',
            last_name='Administrator',
            is_active=True,
            is_verified=True
        )
        admin_user.set_password('admin123')  # Change this in production!
        db.session.add(admin_user)
        db.session.flush()
        
        # Assign admin role
        admin_role = Role.query.filter_by(tenant_id=default_tenant.id, name='Admin').first()
        if admin_role:
            user_role = UserRole(
                user_id=admin_user.id,
                role_id=admin_role.id
            )
            db.session.add(user_role)
    
    db.session.commit()
    print("Database initialized successfully!")
    print("Default admin user created: admin / admin123")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)