# Railway Deployment Guide

## Prerequisites

Before deploying to Railway, ensure you have:
- A Railway account
- A PostgreSQL database provisioned in Railway
- Your repository connected to Railway

## Required Environment Variables

Set these environment variables in your Railway project dashboard:

### Essential Variables

1. **DATABASE_URL** (Required)
   - Provided automatically by Railway PostgreSQL plugin
   - Format: `postgresql://user:password@host:port/database`

2. **SECRET_KEY** (Recommended)
   - Used for JWT token signing
   - Generate a secure random string
   - Example: `openssl rand -hex 32`
   - Default: `dev-secret-key-change-in-production` (insecure!)

### Optional Variables

3. **PORT** (Auto-provided by Railway)
   - Railway automatically sets this
   - Default: 8000

4. **CORS_ORIGINS** (Optional)
   - Comma-separated list of allowed origins
   - Default: `http://localhost:3000,http://localhost:3001`
   - Example: `https://yourdomain.com,https://www.yourdomain.com`

5. **ALGORITHM** (Optional)
   - JWT signing algorithm
   - Default: `HS256`

6. **ACCESS_TOKEN_EXPIRE_MINUTES** (Optional)
   - Token expiry time in minutes
   - Default: `30`

7. **DEBUG** (Optional)
   - Enable debug mode
   - Default: `true`
   - Set to `false` in production

8. **ENVIRONMENT** (Optional)
   - Environment name
   - Default: `development`
   - Set to `production` in Railway

## Deployment Steps

### 1. Create a New Project in Railway

```bash
# Visit https://railway.app/new
# Click "New Project"
# Select "Deploy from GitHub repo"
# Choose your repository
```

### 2. Add PostgreSQL Database

```bash
# In your Railway project:
# Click "New" → "Database" → "Add PostgreSQL"
# Railway will automatically set DATABASE_URL environment variable
```

### 3. Configure Environment Variables

In Railway project settings → Variables, add:

```env
SECRET_KEY=your-secure-random-string-here
CORS_ORIGINS=https://your-frontend-domain.com
ENVIRONMENT=production
DEBUG=false
```

### 4. Deploy

Railway will automatically:
- Detect the `Dockerfile.railway`
- Build the Docker image
- Deploy your application
- Run health checks

### 5. Monitor Deployment

Check the deployment logs in Railway dashboard to ensure:
- ✅ Build completes successfully
- ✅ Application starts without errors
- ✅ Health check passes at `/` endpoint
- ✅ Database connection succeeds

## Health Check

Railway checks the application health at the `/` endpoint:
- Path: `/`
- Timeout: 100 seconds
- Expected response: HTTP 200 with JSON `{"status": "ok"}`

## API Endpoints

After successful deployment, your API will be available at:

- **Root**: `https://your-railway-app.railway.app/`
- **Health**: `https://your-railway-app.railway.app/health`
- **API Docs**: `https://your-railway-app.railway.app/docs`
- **ReDoc**: `https://your-railway-app.railway.app/redoc`

## Troubleshooting

### Build Succeeds but Health Check Fails

**Symptoms**: Build completes but deployment shows "service unavailable"

**Causes**:
1. Missing `SECRET_KEY` environment variable (now has a default)
2. Database connection fails
3. Port binding issues (now fixed to read Railway's PORT env)
4. Application crashes on startup

**Solutions**:
- Check Railway logs for startup errors
- Verify DATABASE_URL is set correctly
- Ensure PostgreSQL database is running
- Check that all required environment variables are set

### Database Connection Errors

**Symptoms**: Logs show "Database initialization failed"

**Note**: The application will still start and pass health checks even if the database is not available. This is intentional to allow the application to start while the database is being provisioned.

**To fix**:
- Verify PostgreSQL plugin is added
- Check DATABASE_URL format in environment variables
- Ensure database is in the same region for better connectivity

### Port Binding Issues

**Symptoms**: "Address already in use" or health check timeout

**Solution**: The app now automatically reads Railway's PORT environment variable. No action needed.

### CORS Errors from Frontend

**Symptoms**: Frontend shows CORS policy errors

**Solution**: Add your frontend domain to CORS_ORIGINS:
```env
CORS_ORIGINS=https://your-frontend.com,https://www.your-frontend.com
```

## Performance Optimization

The `Dockerfile.railway` is optimized for Railway's 4GB image limit:
- Uses `python:3.10-slim` base image
- Installs PyTorch CPU-only version
- Uses `opencv-python-headless` instead of full OpenCV
- Minimal system dependencies

## Security Notes

⚠️ **Important**: Change the SECRET_KEY in production!

The default SECRET_KEY (`dev-secret-key-change-in-production`) is insecure and should only be used for development/testing.

Generate a secure key:
```bash
openssl rand -hex 32
```

Or use Python:
```python
import secrets
print(secrets.token_hex(32))
```

## Monitoring

Monitor your deployment:
- **Logs**: Railway Dashboard → Your Project → Deployment Logs
- **Metrics**: Railway Dashboard → Your Project → Metrics
- **Health**: Visit `https://your-app.railway.app/health`

## Updates and Redeployment

Railway automatically redeploys when you push to your connected branch:
```bash
git add .
git commit -m "Your changes"
git push origin main
```

Railway will:
1. Detect the push
2. Rebuild the Docker image
3. Deploy the new version
4. Run health checks
5. Switch traffic to new deployment if healthy

## Support

If you encounter issues:
1. Check Railway deployment logs
2. Verify all environment variables are set
3. Test database connectivity
4. Check application startup logs
5. Review Railway status page for platform issues
