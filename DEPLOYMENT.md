# Deployment Guide for TaskFlow on Render.com

This guide provides step-by-step instructions for deploying the TaskFlow application to Render.com.

## Prerequisites

- GitHub account
- Render.com account (free tier available)
- Git repository with your code

## Option 1: Automatic Deployment (Recommended)

### Step 1: Prepare Your Repository

1. **Ensure all files are committed**:
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

2. **Verify `render.yaml` exists** in the root directory

### Step 2: Deploy on Render

1. **Log in to Render.com**:
   - Go to [https://render.com](https://render.com)
   - Sign in with GitHub

2. **Create New Blueprint**:
   - Click "New" → "Blueprint"
   - Select your repository
   - Render will detect `render.yaml` automatically

3. **Configure Environment Variables**:
   
   The following variables are auto-configured:
   - `DATABASE_URL` (from PostgreSQL service)
   - `REDIS_URL` (from Redis service)
   - `SECRET_KEY` (auto-generated)
   
   **You need to manually set**:
   - `EMAIL_HOST_USER`: Your SMTP email
   - `EMAIL_HOST_PASSWORD`: Your SMTP password
   
   To add these:
   - Go to each service → Environment
   - Add the variables
   - Click "Save Changes"

4. **Deploy**:
   - Click "Apply" to create all services
   - Wait for deployment (5-10 minutes)
   - Services created:
     - `taskflow-db` (PostgreSQL)
     - `taskflow-redis` (Redis)
     - `taskflow-web` (Django API)
     - `taskflow-celery-worker` (Background tasks)
     - `taskflow-celery-beat` (Periodic tasks)

5. **Access Your Application**:
   - Your API will be at: `https://taskflow-web.onrender.com/api/`
   - Admin: `https://taskflow-web.onrender.com/admin/`
   - Docs: `https://taskflow-web.onrender.com/api/docs/`

### Step 3: Create Superuser

```bash
# Using Render Shell
# Go to taskflow-web service → Shell tab
python manage.py createsuperuser
```

## Option 2: Manual Deployment

If you prefer manual setup or `render.yaml` doesn't work:

### Step 1: Create PostgreSQL Database

1. **New PostgreSQL**:
   - Click "New" → "PostgreSQL"
   - Name: `taskflow-db`
   - Database: `taskflow_db`
   - User: `taskflow_user`
   - Region: Choose closest to you
   - Plan: Free or Starter

2. **Note the connection details**:
   - Internal Database URL (for services)
   - External Database URL (for local access)

### Step 2: Create Redis Instance

1. **New Redis**:
   - Click "New" → "Redis"
   - Name: `taskflow-redis`
   - Region: Same as database
   - Plan: Free or Starter

2. **Note the Redis URL**

### Step 3: Create Web Service

1. **New Web Service**:
   - Click "New" → "Web Service"
   - Connect your repository
   - Name: `taskflow-web`
   - Region: Same as database
   - Branch: `main`
   - Root Directory: Leave empty
   - Environment: `Docker`
   - Plan: Free or Starter

2. **Build Settings**:
   - Dockerfile Path: `./Dockerfile`
   - Docker Context: `.`

3. **Environment Variables**:
   ```
   DJANGO_SETTINGS_MODULE=config.settings.production
   DEBUG=False
   SECRET_KEY=<generate-random-string>
   ALLOWED_HOSTS=.onrender.com
   DATABASE_URL=<from-step-1>
   REDIS_URL=<from-step-2>
   CELERY_BROKER_URL=<same-as-redis-url>
   CELERY_RESULT_BACKEND=<same-as-redis-url>
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=<your-email>
   EMAIL_HOST_PASSWORD=<your-password>
   DEFAULT_FROM_EMAIL=noreply@taskflow.com
   ```

4. **Build Command**:
   ```bash
   pip install -r requirements/production.txt && python manage.py collectstatic --noinput
   ```

5. **Start Command**:
   ```bash
   python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120
   ```

6. **Health Check Path**: `/api/tasks/`

### Step 4: Create Celery Worker

1. **New Background Worker**:
   - Click "New" → "Background Worker"
   - Connect same repository
   - Name: `taskflow-celery-worker`
   - Environment: `Docker`

2. **Use same environment variables as web service**

3. **Start Command**:
   ```bash
   celery -A config worker --loglevel=info --concurrency=2
   ```

### Step 5: Create Celery Beat

1. **New Background Worker**:
   - Name: `taskflow-celery-beat`
   - Environment: `Docker`

2. **Use same environment variables as web service**

3. **Start Command**:
   ```bash
   celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
   ```

## Post-Deployment Steps

### 1. Create Superuser

```bash
# In Render Shell (taskflow-web service)
python manage.py createsuperuser
```

### 2. Test the API

```bash
# Get token
curl -X POST https://your-app.onrender.com/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password"}'

# Create a task
curl -X POST https://your-app.onrender.com/api/tasks/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Task", "priority": "high"}'
```

### 3. Monitor Logs

- Go to each service
- Click "Logs" tab
- Monitor for errors

### 4. Set Up Custom Domain (Optional)

1. Go to `taskflow-web` service
2. Click "Settings" → "Custom Domain"
3. Add your domain
4. Update DNS records as instructed
5. Update `ALLOWED_HOSTS` environment variable

## Troubleshooting

### Database Connection Issues

**Problem**: `could not connect to server`

**Solution**:
- Verify `DATABASE_URL` is set correctly
- Check database service is running
- Ensure web service is in same region

### Static Files Not Loading

**Problem**: CSS/JS not loading in admin

**Solution**:
- Verify `collectstatic` runs in build command
- Check `STATIC_ROOT` and `STATIC_URL` settings
- Ensure WhiteNoise is installed

### Celery Tasks Not Running

**Problem**: Email notifications not sent

**Solution**:
- Check celery worker logs
- Verify `CELERY_BROKER_URL` is correct
- Ensure Redis service is running
- Check email credentials

### Migration Errors

**Problem**: `no such table` errors

**Solution**:
```bash
# In Render Shell
python manage.py migrate --run-syncdb
```

### Memory Issues (Free Tier)

**Problem**: Service crashes due to memory

**Solution**:
- Reduce Celery concurrency: `--concurrency=1`
- Reduce Gunicorn workers: `--workers=2`
- Upgrade to paid plan

## Environment Variables Reference

### Required
- `SECRET_KEY`: Django secret key (auto-generated)
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts

### Optional
- `DEBUG`: Set to `False` in production
- `DJANGO_SETTINGS_MODULE`: `config.settings.production`
- `EMAIL_HOST`: SMTP server (default: smtp.gmail.com)
- `EMAIL_PORT`: SMTP port (default: 587)
- `EMAIL_HOST_USER`: Your email
- `EMAIL_HOST_PASSWORD`: Your email password
- `SENTRY_DSN`: Sentry error tracking (optional)

## Scaling on Render

### Horizontal Scaling

1. **Web Service**:
   - Go to service settings
   - Increase instance count
   - Render load balances automatically

2. **Celery Workers**:
   - Create additional worker services
   - All connect to same Redis broker

### Vertical Scaling

- Upgrade service plan for more RAM/CPU
- Recommended for database and Redis

## Monitoring

### Built-in Monitoring

- Render provides:
  - CPU usage
  - Memory usage
  - Request metrics
  - Error rates

### External Monitoring (Optional)

1. **Sentry** (Error Tracking):
   - Sign up at sentry.io
   - Add `SENTRY_DSN` to environment variables
   - Errors automatically reported

2. **New Relic** (APM):
   - Add to requirements
   - Configure in settings

## Backup Strategy

### Database Backups

- Render automatically backs up PostgreSQL
- Retention: 7 days (free), 30 days (paid)
- Manual backup:
  ```bash
  pg_dump $DATABASE_URL > backup.sql
  ```

### Redis Backups

- Redis persistence enabled by default
- Data saved to disk periodically

## Cost Optimization

### Free Tier Limits

- Web Service: Spins down after 15 min inactivity
- Database: 1GB storage
- Redis: 25MB storage

### Recommendations

1. **Use Starter Plan** for production ($7/month per service)
2. **Combine services** where possible
3. **Monitor usage** to avoid overages
4. **Use caching** to reduce database load

## Security Checklist

- ✅ `DEBUG=False` in production
- ✅ Strong `SECRET_KEY`
- ✅ `ALLOWED_HOSTS` properly configured
- ✅ HTTPS enforced (automatic on Render)
- ✅ Database credentials secured
- ✅ Email credentials in environment variables
- ✅ CORS configured if needed
- ✅ Rate limiting enabled

## Maintenance

### Updating the Application

```bash
# Local
git add .
git commit -m "Update feature"
git push origin main

# Render auto-deploys on push (if enabled)
# Or manually trigger deploy in Render dashboard
```

### Running Migrations

```bash
# Migrations run automatically on deploy
# Or manually in Shell:
python manage.py migrate
```

### Database Management

```bash
# Access database
# In Render Shell:
python manage.py dbshell

# Or use external tool with External Database URL
```

## Support

- **Render Docs**: https://render.com/docs
- **Render Community**: https://community.render.com
- **Django Docs**: https://docs.djangoproject.com

## Next Steps

1. ✅ Deploy application
2. ✅ Create superuser
3. ✅ Test API endpoints
4. ✅ Configure custom domain
5. ✅ Set up monitoring
6. ✅ Configure backups
7. ✅ Enable auto-deploy on git push

---

**Congratulations!** Your TaskFlow application is now running in production on Render.com! 🎉
