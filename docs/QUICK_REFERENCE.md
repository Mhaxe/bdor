# Quick Reference Card

## 🚀 Django + React Integration Patterns

### Current Setup: Catch-All Route

**URLs Configuration:**
```python
# balon_dor/urls.py
from django.urls import path, re_path
from core.views import IndexView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    re_path(r'^.*', IndexView.as_view(), name='index'),  # Catches all routes
]
```

**View:**
```python
# core/views.py
from django.views.generic import TemplateView

class IndexView(TemplateView):
    template_name = "index.html"
```

**Use When:**
- ✅ Rapid development/prototyping
- ✅ Many dynamic user-generated routes
- ✅ Internal tools with less security concern

---

## 🔒 Production Pattern: Explicit Routes

**URLs Configuration:**
```python
# balon_dor/urls.py
from django.urls import path, re_path
from core.views import IndexView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    
    # Explicit routes - only these work
    path('', IndexView.as_view(), name='home'),
    path('route-1/', IndexView.as_view(), name='route-1'),
    path('route-2/', IndexView.as_view(), name='route-2'),
    path('dashboard/', IndexView.as_view(), name='dashboard'),
    
    # For nested routes, use pattern matching
    re_path(r'^products/.*', IndexView.as_view(), name='products'),
    re_path(r'^blog/.*', IndexView.as_view(), name='blog'),
]
```

**Use When:**
- ✅ Production deployment
- ✅ Security requirements
- ✅ Need proper 404 handling
- ✅ SEO matters
- ✅ Defined route structure

---

## 📦 Common Commands

### Frontend
```bash
# Development with hot reload
cd frontend
bun run dev

# Build for production
cd frontend
bun run build

# Lint
cd frontend
bun run lint
```

### Backend
```bash
# Development server
python manage.py runserver

# Run all Django tests
python manage.py test

# Run a single Django test method
python manage.py test api.tests.SomeTestCase.test_method_name

# Migrations
python manage.py makemigrations
python manage.py migrate

# Collect static files (production)
python manage.py collectstatic

# Create admin user
python manage.py createsuperuser
```

### All-in-One
```bash
# Build frontend and start Django
./start.sh
```

---

## Debugging Django

### Quick `breakpoint()` Debugging

Use Python's built-in debugger directly in backend code:

```python
def get_player_rankings():
    players_records = DataNormalizationService.normalize_data()
    breakpoint()
    return players_records
```

You do not need to import `breakpoint()` in this project because it is a Python built-in.

Run the app or a test, then use these `pdb` commands:

| Command | Meaning |
|---------|---------|
| `n` | Step over the next line |
| `s` | Step into a function call |
| `r` | Run until the current function returns |
| `c` | Continue execution |
| `l` | Show code around the current line |
| `p value` | Print a value |
| `pp value` | Pretty-print a value |
| `q` | Quit the debugger |

### VS Code Breakpoint Debugging

This repository includes `.vscode/launch.json` with Django debug targets.

Available configurations:
- `Django Runserver`
- `Django Test`

How to use it:
1. Open a backend file such as `api/views.py` or `api/services/player_ranking_service.py`
2. Click in the gutter to add a breakpoint
3. Open the Run and Debug panel in VS Code
4. Choose `Django Runserver` or `Django Test`
5. Press `F5` to start debugging

Useful VS Code shortcuts:

| Shortcut | Meaning |
|----------|---------|
| `F10` | Step over |
| `F11` | Step into |
| `Shift+F11` | Step out |
| `F5` | Continue |

### Good Backend Files to Debug

- `api/views.py`
- `api/services/external_stats_service.py`
- `api/services/data_normalization_service.py`
- `api/services/player_ranking_service.py`

---

## 🔧 View Patterns

### Basic View
```python
class IndexView(TemplateView):
    template_name = "index.html"
```

### With Authentication
```python
from django.contrib.auth.mixins import LoginRequiredMixin

class PrivateView(LoginRequiredMixin, TemplateView):
    template_name = "index.html"
    login_url = '/login/'
```

### With Admin Permission
```python
from django.contrib.auth.mixins import PermissionRequiredMixin

class AdminView(PermissionRequiredMixin, TemplateView):
    template_name = "index.html"
    permission_required = 'auth.is_staff'
```

### With Caching
```python
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

@method_decorator(cache_page(60 * 15), name='dispatch')
class CachedView(TemplateView):
    template_name = "index.html"
```

### With Context Data
```python
class ContextView(TemplateView):
    template_name = "index.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_name'] = 'Balon d\'Or'
        context['user_data'] = self.request.user
        return context
```

---

## 🌐 URL Structure

| Path | Handler | Purpose |
|------|---------|---------|
| `/` | React | Frontend home |
| `/route-1/` | React | Example route 1 |
| `/route-2/` | React | Example route 2 |
| `/admin/` | Django | Admin interface |
| `/api/*` | Django | API endpoints |

---

## 🔍 Testing Routes

### Test Specific Route
```bash
# Should return 200
curl -I http://localhost:8000/route-1/

# Should return 404 (with explicit routes)
curl -I http://localhost:8000/nonexistent/
```

### Test in Browser
```
http://localhost:8000/           # Home
http://localhost:8000/route-1/   # Route 1
http://localhost:8000/admin/     # Django admin
```

---

## 📁 File Structure

```
balon-dor/
├── balon_dor/
│   ├── settings.py          # Django config
│   └── urls.py              # URL routing
├── core/
│   └── views.py             # React view classes
├── frontend/
│   ├── src/                 # React source
│   └── dist/                # Built files
├── docs/
│   ├── DEPLOYMENT.md        # Deployment guide
│   ├── EXPLICIT_ROUTES.md   # Explicit routes pattern
│   ├── CBV_REFERENCE.md     # View reference
│   └── MIGRATION_CHECKLIST.md  # Migration guide
└── start.sh                 # Quick start script
```

---

## 🚨 Common Issues

### Static Files Not Loading
```bash
cd frontend && bun run build
python manage.py runserver
# Clear browser cache (Ctrl+Shift+R)
```

### React Routes Return 404
```python
# Ensure catch-all is LAST in urls.py
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    re_path(r'^.*', IndexView.as_view()),  # Must be last!
]
```

### Changes Not Reflecting
1. Rebuild React: `cd frontend && bun run build`
2. Restart Django server
3. Clear browser cache

---

## 📊 Routing Pattern Comparison

| Feature | Catch-All | Explicit Routes |
|---------|-----------|-----------------|
| Security | ⚠️ Lower | ✅ Higher |
| 404 Handling | ❌ Returns React app | ✅ Proper 404 |
| Setup Complexity | ✅ Simple | ⚠️ More verbose |
| Maintenance | ✅ Auto handles new routes | ⚠️ Manual updates needed |
| SEO | ⚠️ All invalid URLs load | ✅ Proper error pages |
| Route-Specific Logic | ❌ Harder | ✅ Easy per route |
| Best For | Development | Production |

---

## 💡 Pro Tips

1. **Development:** Use catch-all for rapid iteration
2. **Production:** Switch to explicit routes for security
3. **Sync Routes:** Keep React and Django routes documented
4. **API First:** Add API routes before catch-all/React routes
5. **Cache Public Routes:** Use caching for better performance
6. **Test 404s:** Verify invalid routes return proper errors

---

## 📚 Documentation Map

| Document | Purpose |
|----------|---------|
| `README.md` | Project overview & quick start |
| `SETUP_COMPLETE.md` | What was configured |
| `docs/DEPLOYMENT.md` | Production deployment |
| `docs/EXPLICIT_ROUTES.md` | Explicit routes pattern ⭐ |
| `docs/DATABASE_TABLES.md` | Database table reference |
| `docs/MIGRATION_CHECKLIST.md` | Migration guide |
| `docs/CBV_REFERENCE.md` | View class reference |
| `docs/QUICK_REFERENCE.md` | This document |

---

## 🎯 Next Steps

1. **Develop:** Build your React app with current catch-all setup
2. **Review:** When ready for production, review `EXPLICIT_ROUTES.md`
3. **Migrate:** Follow `MIGRATION_CHECKLIST.md` to switch patterns
4. **Deploy:** Use `DEPLOYMENT.md` for production deployment

---

**Version:** 1.0  
**Last Updated:** 2024  
**Project:** Balon d'Or - Django + React Full-Stack Application
