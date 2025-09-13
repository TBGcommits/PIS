# TBG-PIS - Multi-tenant Project Management System

نظام إدارة مشاريع متكامل متعدد الشركات واللغات (TBG-PIS) باستخدام بايثون

## Features | الميزات | Características

- **Multi-tenancy** | **تعدد الشركات** | **Multi-inquilino**: Complete data isolation between companies
- **Multi-language** | **تعدد اللغات** | **Multi-idioma**: Arabic (RTL), English, Spanish support
- **RBAC Security** | **نظام صلاحيات** | **Seguridad RBAC**: Role-based access control
- **Audit Trail** | **سجل التدقيق** | **Registro de auditoría**: Immutable audit logging
- **Project Management** | **إدارة المشاريع** | **Gestión de proyectos**: Complete project lifecycle management
- **Field Operations** | **العمليات الميدانية** | **Operaciones de campo**: Daily logs, attendance, material requests
- **Dashboard & Reports** | **لوحة التحكم والتقارير** | **Panel e informes**: Real-time project monitoring

## Technology Stack | التقنيات المستخدمة | Pila tecnológica

### Backend
- **Python 3.12** with Flask framework
- **SQLite/MySQL** database with SQLAlchemy ORM
- **JWT Authentication** for secure API access
- **Flask-Migrate** for database migrations
- **CORS** enabled for frontend integration

### Frontend
- **HTML5/CSS3/JavaScript** with Bootstrap 5
- **Multi-language** support with JSON resource files
- **Responsive design** for mobile and desktop
- **RTL support** for Arabic language

## Installation & Setup | التثبيت والإعداد | Instalación y configuración

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env file with your configuration
FLASK_APP=run.py flask init-db
python run.py
```

### Frontend Setup

```bash
cd frontend
python -m http.server 8080
# Or use any web server like nginx, apache, etc.
```

## Default Credentials | بيانات الدخول الافتراضية | Credenciales predeterminadas

- **Username**: admin
- **Password**: admin123
- **Tenant**: default

⚠️ **Change these credentials in production!**

## API Endpoints | نقاط الاتصال | Endpoints de API

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `GET /api/auth/profile` - Get user profile
- `PUT /api/auth/profile` - Update user profile

### Projects
- `GET /api/projects/` - List projects
- `POST /api/projects/` - Create project
- `GET /api/projects/{id}` - Get project details
- `PUT /api/projects/{id}` - Update project

### Tasks
- `GET /api/projects/{id}/tasks` - List project tasks
- `POST /api/projects/{id}/tasks` - Create task

### Field Operations
- `POST /api/field-ops/daily-log` - Create daily log
- `POST /api/field-ops/attendance` - Record attendance
- `POST /api/field-ops/material-request` - Request materials
- `GET /api/field-ops/operations` - List operations

### Dashboard
- `GET /api/dashboard/stats` - Get dashboard statistics
- `GET /api/dashboard/recent-activity` - Get recent activity
- `GET /api/dashboard/my-tasks` - Get user's tasks

## Multi-tenant Usage | استخدام تعدد الشركات | Uso multi-inquilino

All API requests must include the `X-Tenant` header:

```bash
curl -H "X-Tenant: default" -H "Authorization: Bearer <token>" \
  http://localhost:5001/api/projects/
```

## Language Support | دعم اللغات | Soporte de idiomas

The system supports three languages:

- **English (en)** - Default language
- **Arabic (ar)** - Right-to-left (RTL) support
- **Spanish (es)** - Full translation support

Language files are located in:
- Backend: `backend/app/locales/`
- Frontend: `frontend/locales/`

## Security Features | ميزات الأمان | Características de seguridad

- **JWT Token Authentication** with secure token handling
- **Role-Based Access Control (RBAC)** with granular permissions
- **Multi-tenant Data Isolation** - complete data separation
- **Audit Trail** - immutable logging of all system actions
- **Password Hashing** with bcrypt
- **CORS Protection** for API security

## Database Schema | مخطط قاعدة البيانات | Esquema de base de datos

### Core Tables
- `tenants` - Multi-tenant organizations
- `users` - User accounts with tenant isolation
- `roles` - RBAC role definitions
- `permissions` - System permissions
- `user_roles` - User-role assignments
- `role_permissions` - Role-permission mappings

### Project Management
- `projects` - Project definitions
- `project_modules` - Hierarchical project modules
- `tasks` - Project tasks
- `project_teams` - Team member assignments

### Operations
- `field_operations` - Field operations and daily logs
- `audit_logs` - Immutable audit trail

## Development | التطوير | Desarrollo

### Running Tests
```bash
cd backend
python -m pytest tests/
```

### Database Migrations
```bash
cd backend
flask db init
flask db migrate -m "Description"
flask db upgrade
```

### Adding New Languages
1. Create new JSON file in `locales/` directories
2. Add language code to `LANGUAGES` in config
3. Update language switcher in frontend

## Production Deployment | النشر في الإنتاج | Despliegue en producción

### Backend
- Use a production WSGI server (gunicorn, uwsgi)
- Configure proper database (PostgreSQL, MySQL)
- Set secure environment variables
- Enable HTTPS

### Frontend
- Use a production web server (nginx, apache)
- Configure HTTPS
- Enable gzip compression
- Set proper cache headers

### Environment Variables
```bash
SECRET_KEY=your-secure-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
DATABASE_URL=your-production-database-url
FLASK_ENV=production
```

## Contributing | المساهمة | Contribuyendo

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Submit a pull request

## License | الترخيص | Licencia

This project is open source and available under the MIT License.

## Support | الدعم | Soporte

For support, please create an issue in the GitHub repository or contact the development team.

---

**TBG-PIS** - Built with ❤️ for construction project management
