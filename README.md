# TaskFlow - Production-Ready Django REST Framework Application

A comprehensive, production-grade Django REST Framework application demonstrating clean architecture, proxy models, background tasks, caching, and full Docker deployment.

## 🎯 Project Overview

TaskFlow is a **Task Management System** built with Django REST Framework, showcasing enterprise-level architecture and best practices:

- **Clean Architecture** with service layer separation
- **Proxy Models** for behavioral inheritance without table duplication
- **Celery** for asynchronous task processing
- **Redis** for caching and message brokering
- **Docker** multi-service deployment
- **Production-ready** security and configuration

## 🏗️ Architecture

```
┌─────────────┐
│   Nginx     │ ← Reverse Proxy + Static Files
└──────┬──────┘
       │
┌──────▼──────┐
│  Django API │ ← REST Framework + Business Logic
└──────┬──────┘
       │
┌──────▼──────┬──────────┬──────────┐
│ PostgreSQL  │  Redis   │  Celery  │
└─────────────┴──────────┴──────────┘
```

### Key Components

1. **API Layer**: Django REST Framework with ViewSets
2. **Service Layer**: Business logic separation
3. **Model Layer**: Task + CompletedTask (proxy model)
4. **Background Tasks**: Celery for async operations
5. **Caching**: Redis for performance optimization
6. **Reverse Proxy**: Nginx for production deployment

## 📦 Features

### Core Functionality
- ✅ Full CRUD operations for tasks
- ✅ Task status management (pending, in_progress, completed)
- ✅ Priority levels (low, medium, high)
- ✅ User assignment and ownership
- ✅ Soft delete with audit trail
- ✅ Due date tracking and overdue detection

### Advanced Features
- ✅ **Proxy Model**: CompletedTask for specialized behavior
- ✅ **Custom Managers**: Chainable querysets (active, completed, overdue)
- ✅ **Service Layer**: Reusable business logic
- ✅ **Celery Tasks**: Async email notifications
- ✅ **Redis Caching**: Performance optimization
- ✅ **JWT Authentication**: Secure API access
- ✅ **Rate Limiting**: API protection
- ✅ **Filtering & Search**: Advanced querying
- ✅ **Pagination**: Efficient data loading
- ✅ **OpenAPI Documentation**: Auto-generated API docs

### API Endpoints

#### Tasks
- `GET /api/tasks/` - List all tasks
- `POST /api/tasks/` - Create new task
- `GET /api/tasks/{id}/` - Get task details
- `PUT /api/tasks/{id}/` - Update task
- `PATCH /api/tasks/{id}/` - Partial update
- `DELETE /api/tasks/{id}/` - Soft delete task
- `POST /api/tasks/{id}/complete/` - Mark as complete
- `GET /api/tasks/statistics/` - Get user statistics
- `GET /api/tasks/overdue/` - Get overdue tasks
- `POST /api/tasks/bulk_assign/` - Bulk assign tasks

#### Completed Tasks (Proxy Model)
- `GET /api/completed-tasks/` - List completed tasks
- `GET /api/completed-tasks/{id}/` - Get completed task details
- `GET /api/completed-tasks/recent/` - Recently completed
- `GET /api/completed-tasks/report/` - Completion report

#### Authentication
- `POST /api/token/` - Obtain JWT token
- `POST /api/token/refresh/` - Refresh JWT token

#### Documentation
- `GET /api/docs/` - Swagger UI
- `GET /api/redoc/` - ReDoc UI
- `GET /api/schema/` - OpenAPI schema

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL 15+ (for local development)
- Redis 7+ (for local development)

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd task_flow_app

# Copy environment file
cp .env.example .env

# Edit .env with your settings
nano .env
```

### 2. Docker Deployment (Recommended)

```bash
# Build and start all services
docker-compose up --build

# The application will be available at:
# - API: http://localhost/api/
# - Admin: http://localhost/admin/
# - Swagger Docs: http://localhost/api/docs/
```

**Default superuser** (development only):
- Username: `admin`
- Password: `admin123`

### 3. Local Development (Without Docker)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements/development.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic

# Run development server
python manage.py runserver

# In separate terminals:
# Start Celery worker
celery -A config worker --loglevel=info

# Start Celery beat
celery -A config beat --loglevel=info
```

## 🐳 Docker Services

The application runs 6 Docker services:

1. **db** - PostgreSQL 15 database
2. **redis** - Redis 7 for caching and Celery
3. **web** - Django application (Gunicorn)
4. **celery_worker** - Background task processor
5. **celery_beat** - Periodic task scheduler
6. **nginx** - Reverse proxy and static file server

### Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Rebuild after code changes
docker-compose up --build

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Access Django shell
docker-compose exec web python manage.py shell

# Access database
docker-compose exec db psql -U taskflow_user -d taskflow_db
```

## 🎭 Proxy Model Explained

### Why Proxy Model?

The `CompletedTask` proxy model demonstrates a powerful Django pattern:

**Same Table, Different Behavior**

```python
# Base model
class Task(models.Model):
    # All fields and logic
    pass

# Proxy model - NO new table created!
class CompletedTask(Task):
    class Meta:
        proxy = True
    
    # Custom manager filters only completed tasks
    objects = CompletedTaskManager()
    
    # Specialized methods for completed tasks
    def days_since_completion(self):
        ...
```

**Benefits**:
1. ✅ No database table duplication
2. ✅ Specialized querysets and methods
3. ✅ Different admin interface
4. ✅ Clean API separation (`/api/tasks/` vs `/api/completed-tasks/`)
5. ✅ Performance - same table, optimized queries

**vs. Abstract Inheritance**:
- ❌ Would create separate tables
- ❌ Data duplication

**vs. Multi-Table Inheritance**:
- ❌ Additional table with JOIN overhead
- ❌ Unnecessary complexity

**Use Cases**:
- Different default ordering
- Specialized business methods
- Separate admin interfaces
- API endpoint separation
- Report generation

## 🔧 Configuration

### Environment Variables

Key environment variables (see `.env.example`):

```bash
# Django
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://user:pass@host:port/db

# Redis
REDIS_URL=redis://redis:6379/0

# Celery
CELERY_BROKER_URL=redis://redis:6379/0

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-password
```

### Settings Structure

```
config/settings/
├── __init__.py
├── base.py          # Common settings
├── development.py   # Dev-specific (DEBUG=True)
└── production.py    # Production (security hardened)
```

## 🌐 Render.com Deployment

### Automatic Deployment

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Connect to Render.com**:
   - Go to [Render.com](https://render.com)
   - Click "New" → "Blueprint"
   - Connect your GitHub repository
   - Render will automatically detect `render.yaml`

3. **Configure Environment Variables**:
   - Set `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD`
   - Other variables are auto-configured

4. **Deploy**:
   - Render will create all services automatically
   - Wait for deployment to complete
   - Access your API at `https://your-app.onrender.com/api/`

### Manual Deployment Steps

If not using `render.yaml`:

1. **Create PostgreSQL Database**:
   - Name: `taskflow-db`
   - Plan: Starter

2. **Create Redis Instance**:
   - Name: `taskflow-redis`
   - Plan: Starter

3. **Create Web Service**:
   - Name: `taskflow-web`
   - Environment: Docker
   - Build Command: `pip install -r requirements/production.txt && python manage.py collectstatic --noinput`
   - Start Command: `python manage.py migrate && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`

4. **Create Celery Worker**:
   - Name: `taskflow-celery-worker`
   - Environment: Docker
   - Start Command: `celery -A config worker --loglevel=info`

5. **Create Celery Beat**:
   - Name: `taskflow-celery-beat`
   - Environment: Docker
   - Start Command: `celery -A config beat --loglevel=info`

## 📊 API Usage Examples

### Authentication

```bash
# Obtain token
curl -X POST http://localhost/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Response: {"access": "...", "refresh": "..."}
```

### Create Task

```bash
curl -X POST http://localhost/api/tasks/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Complete project documentation",
    "description": "Write comprehensive README",
    "priority": "high",
    "due_date": "2026-02-15T12:00:00Z"
  }'
```

### List Tasks with Filtering

```bash
# Get high priority pending tasks
curl "http://localhost/api/tasks/?priority=high&status=pending" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Search tasks
curl "http://localhost/api/tasks/?search=documentation" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Order by due date
curl "http://localhost/api/tasks/?ordering=due_date" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Complete Task

```bash
curl -X POST http://localhost/api/tasks/1/complete/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Get Statistics

```bash
curl http://localhost/api/tasks/statistics/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🏛️ Project Structure

```
task_flow_app/
├── config/                      # Project configuration
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── celery.py
│   ├── urls.py
│   └── wsgi.py
├── tasks/                       # Main application
│   ├── models/
│   │   ├── task.py             # Base Task model
│   │   ├── proxy.py            # CompletedTask proxy
│   │   └── managers.py         # Custom managers
│   ├── services/
│   │   └── task_service.py     # Business logic
│   ├── serializers/
│   │   └── task_serializer.py  # API serializers
│   ├── views/
│   │   └── task_viewset.py     # API viewsets
│   ├── tasks.py                # Celery tasks
│   ├── signals.py              # Django signals
│   ├── admin.py                # Admin interface
│   └── urls.py                 # URL routing
├── core/                        # Shared utilities
│   ├── exceptions.py
│   ├── pagination.py
│   └── permissions.py
├── docker/
│   ├── nginx/
│   │   └── nginx.conf
│   └── entrypoint.sh
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
├── Dockerfile
├── docker-compose.yml
├── render.yaml
├── manage.py
└── README.md
```

## 🔒 Security Features

- ✅ JWT authentication
- ✅ Rate limiting (100/hour for anonymous, 1000/hour for authenticated)
- ✅ HTTPS enforcement in production
- ✅ Secure cookies (CSRF, Session)
- ✅ XSS protection headers
- ✅ SQL injection prevention (ORM)
- ✅ Non-root Docker user
- ✅ Environment-based secrets
- ✅ Nginx security headers

## 📝 Development

### Running Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test tasks

# With coverage
pytest --cov=tasks --cov-report=html
```

### Code Quality

```bash
# Format code
black .

# Lint
flake8

# Type checking
mypy .
```

### Database Migrations

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migrations
python manage.py showmigrations
```

## 🎓 Learning Points

This project demonstrates:

1. **Clean Architecture**: Separation of concerns (API → Service → Model)
2. **Proxy Models**: Behavioral inheritance without table duplication
3. **Service Layer**: Reusable business logic
4. **Celery Integration**: Async task processing
5. **Redis Caching**: Performance optimization
6. **Docker Multi-Service**: Production deployment
7. **Nginx Configuration**: Reverse proxy and static files
8. **Security Best Practices**: Production-ready security
9. **API Design**: RESTful endpoints with filtering/pagination
10. **Documentation**: OpenAPI/Swagger integration

## 📚 Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Docker Documentation](https://docs.docker.com/)
- [Render.com Docs](https://render.com/docs)

## 📄 License

This project is for educational purposes.

## 👨‍💻 Author

Built as a production-ready example of Django REST Framework best practices.

---

**Need Help?**
- Check the API documentation at `/api/docs/`
- Review the admin interface at `/admin/`
- Check Docker logs: `docker-compose logs -f`
