# EduStory Backend - Development Mode Guide

## Overview
This backend supports two modes:
- **Production**: Full database connectivity with MySQL
- **Development**: No database required, uses mock data

## Quick Start for Development

### 1. Environment Setup
```bash
# Use development environment
cp .env.development .env
```

### 2. Run Backend
```bash
python main.py
```

The backend will automatically detect `ENV=development` and:
- ✓ Skip database initialization
- ✓ Skip authentication (auto-login as dev user)
- ✓ Skip email services
- ✓ Enable all story generation features

### 3. Development User
When `ENV=development`, you're automatically logged in as:
- **Email**: `dev@local`
- **Username**: `developer`
- **Admin**: Yes
- **Premium**: Yes
- **Verified**: Yes

## API Endpoints (Development Mode)

All endpoints work normally except:
- `/api/auth/signup` - Returns mock success
- `/api/auth/token` - Returns dev token
- `/api/auth/me` - Returns dev user
- Database operations are skipped

## Production Deployment

For production, use standard `.env` with real MySQL credentials:
```bash
# Production environment
MYSQL_HOST=your-vps-ip
MYSQL_USER=edusmart
MYSQL_PASSWORD=secure-password
MYSQL_DATABASE=edusmart
ENV=production
```

## Docker Deployment

Your webhook system will:
1. Pull latest code from GitHub
2. Build Docker containers
3. Use production `.env` from VPS
4. Connect to MySQL on VPS

## Safety Features

- ✅ No database errors in development
- ✅ No network dependencies for local dev
- ✅ Production mode requires valid DB connection
- ✅ Environment-specific startup messages

## Troubleshooting

**Issue**: Database connection errors
**Solution**: Ensure `ENV=development` in `.env`

**Issue**: Frontend can't connect to backend
**Solution**: Check `API_HOST=0.0.0.0` and port 8000

**Issue**: Webhook deployment fails
**Solution**: Verify production `.env` exists on VPS
