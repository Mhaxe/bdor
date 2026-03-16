# Deployment Guide: Serving React Frontend from Django

This guide explains how the React frontend is integrated with Django in this project.

## Architecture

This project uses a **single-server deployment** where Django serves both:
- The pre-built React frontend (static files + SPA)
- Django admin interface
- API endpoints (when added)

## Project Structure

```
balon-dor/
├── balon_dor/           # Django project settings
│   ├── settings.py      # Configured to serve React build
│   └── urls.py          # Routes with catch-all for React Router
├── core/                # Django app for frontend views
│   └── views.py         # Index view that renders React app
├── frontend/            # React + Vite + TypeScript
│   ├── src/             # React source code
│   └── dist/            # Built React app (generated)
│       ├── index.html   # Main HTML file served by Django
│       └── assets/      # Compiled JS, CSS, images
└── manage.py
```

## Development Workflow

### 1. Develop React Frontend

```bash
cd frontend
bun run dev
```

This runs Vite dev server at `http://localhost:5173` with hot module replacement.

### 2. Build React for Production

When ready to test the Django integration:

```bash
cd frontend
bun run build
```

This creates optimized production files in `frontend/dist/`:
- `index.html` - Main entry point
- `assets/` - Bundled JavaScript, CSS, and images

### 3. Run Django Server

```bash
python manage.py runserver
```

Django now serves:
- `http://localhost:8000/` - React app (catch-all route)
- `http://localhost:8000/admin/` - Django admin
- `http://localhost:8000/api/*` - Your API endpoints (when added)

## How It Works

### Django Configuration (`settings.py`)

```python
# Templates: Where Django looks for index.html
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'frontend', 'dist')],
        ...
    },
]

# Static files: Where Django finds JS/CSS/images
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'frontend', 'dist', 'assets'),
]
```

### URL Routing (`urls.py`)

```python
urlpatterns = [
    path('admin/', admin.site.urls),
    # Add API routes here
    # path('api/', include('your_api.urls')),
    
    # Catch-all for React Router (MUST BE LAST)
    re_path(r'^.*', index, name='index'),
]
```

The `re_path(r'^.*', ...)` catch-all route ensures that:
- Any unmatched URL loads `index.html`
- React Router takes over client-side routing
- URLs like `/about`, `/profile`, etc. work correctly

**Note:** For production applications, consider using **explicit routes** instead of catch-all:
```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('your_api.urls')),
    
    # Explicitly define each React route
    path('', IndexView.as_view(), name='home'),
    path('route-1/', IndexView.as_view(), name='route-1'),
    path('route-2/', IndexView.as_view(), name='route-2'),
    # No catch-all - invalid routes return proper 404
]
```

This approach provides better security, proper 404 handling, and self-documentation. See `docs/EXPLICIT_ROUTES.md` for detailed guidance.

### View (`core/views.py`)

```python
from django.views.generic import TemplateView

class IndexView(TemplateView):
    """
    Serves the main index.html file of the React application.
    This view acts as the entry point for the React SPA.
    """
    template_name = "index.html"
```

Class-based view that returns the React app's main HTML file.

## Production Deployment

### 1. Environment Setup

Create a production settings file or use environment variables:

```python
# settings.py or settings_prod.py
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

# Uncomment this for production
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
```

### 2. Build React

```bash
cd frontend
bun run build
```

### 3. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

This gathers all static files (including React assets) into `STATIC_ROOT` for efficient serving.

### 4. Use Production Server

Don't use `runserver` in production. Use:
- **Gunicorn** or **uWSGI** for Django application
- **Nginx** or **Apache** for serving static files and reverse proxy

Example with Gunicorn:

```bash
gunicorn balon_dor.wsgi:application --bind 0.0.0.0:8000
```

### 5. Nginx Configuration Example

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Serve static files directly
    location /static/ {
        alias /path/to/balon-dor/staticfiles/;
    }

    # Proxy other requests to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Common Issues & Solutions

### Static files not loading

**Problem:** JS/CSS files return 404 errors.

**Solution:** 
1. Check `STATICFILES_DIRS` in `settings.py`
2. Rebuild React: `cd frontend && bun run build`
3. In production, run: `python manage.py collectstatic`

### React Router routes return 404

**Problem:** URLs like `/about` show Django 404 page.

**Solution:** Ensure the catch-all `re_path(r'^.*', index)` is the **last** URL pattern.

### API routes not working

**Problem:** API endpoints are caught by React catch-all route.

**Solution:** Add API routes **before** the catch-all:

```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('api.urls')),  # Add before catch-all
    re_path(r'^.*', index),  # Keep last
]
```

### Changes not reflecting

**Problem:** Frontend changes don't appear after rebuilding.

**Solutions:**
1. Clear browser cache (Ctrl+Shift+R / Cmd+Shift+R)
2. Rebuild React: `cd frontend && bun run build`
3. Restart Django server
4. In production, run `collectstatic` again

## Adding API Endpoints

When you add Django REST Framework or API views:

```python
# urls.py
from django.urls import path, include, re_path
from core.views import IndexView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('authentication.urls')),
    path('api/data/', include('api.urls')),
    # Add all API routes above this line
    re_path(r'^.*', IndexView.as_view()),  # React catch-all stays last
]
```

## Benefits of This Approach

✅ **Single deployment** - One server, one domain  
✅ **No CORS issues** - Frontend and backend on same origin  
✅ **Simplified hosting** - Deploy as single application  
✅ **Django session/auth** - Works seamlessly with React  
✅ **Cost effective** - One server instead of two  

## Alternative: Separate Deployments

For larger applications, consider deploying separately:
- Frontend: Vercel, Netlify, or CDN
- Backend: Heroku, Railway, or VPS

This requires CORS configuration and separate domains.

---

**Last Updated:** 2024