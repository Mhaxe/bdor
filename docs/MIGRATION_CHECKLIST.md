# Migration Checklist: Catch-All to Explicit Routes

This checklist guides you through migrating from the catch-all route pattern to explicit routes for better control and security.

## 📋 Pre-Migration Checklist

### Step 1: Document Current React Routes

- [ ] List all routes defined in your React Router configuration
- [ ] Note any dynamic routes (e.g., `/products/:id`, `/blog/:slug`)
- [ ] Identify nested routes (e.g., `/dashboard/settings/profile`)
- [ ] Document route purposes and requirements

**Tool to help:**
```bash
# Find route definitions in React code
cd frontend/src
grep -r "path=" . | grep -o 'path="[^"]*"' | sort -u
```

### Step 2: Categorize Your Routes

Group routes by access level:

- [ ] **Public routes** - No authentication required
- [ ] **Authenticated routes** - Login required
- [ ] **Admin routes** - Admin/staff permissions required
- [ ] **Dynamic routes** - Routes with parameters or nested paths

### Step 3: Create Route Configuration

- [ ] Copy `core/routes_config.py.example` to `core/routes_config.py`
- [ ] Update `PUBLIC_ROUTES` with your public routes
- [ ] Update `AUTHENTICATED_ROUTES` with protected routes
- [ ] Update `ADMIN_ROUTES` with admin-only routes
- [ ] Update `DYNAMIC_ROUTES` with pattern-matched routes
- [ ] Add descriptions for each route

### Step 4: Create View Classes (if needed)

If you want different behavior for different route types:

- [ ] Create `PublicReactView` (optional caching)
- [ ] Create `PrivateReactView` (authentication required)
- [ ] Create `AdminReactView` (admin permissions required)

**Example in `core/views.py`:**
```python
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import TemplateView


class BaseReactView(TemplateView):
    """Base view for all React routes"""
    template_name = "index.html"


class PublicReactView(BaseReactView):
    """Public routes - no authentication required"""
    pass


class PrivateReactView(LoginRequiredMixin, BaseReactView):
    """Authenticated routes - login required"""
    login_url = '/login/'
    redirect_field_name = 'next'


class AdminReactView(PermissionRequiredMixin, BaseReactView):
    """Admin routes - staff/admin permissions required"""
    permission_required = 'auth.is_staff'
    login_url = '/admin/login/'
```

---

## 🔄 Migration Process

### Phase 1: Add Explicit Routes (Keep Catch-All)

Add explicit routes alongside the catch-all for testing:

- [ ] Update `urls.py` with explicit routes
- [ ] Keep catch-all route as last item
- [ ] Verify all explicit routes work correctly

**Example `urls.py`:**
```python
from django.contrib import admin
from django.urls import path, include, re_path

from core.views import IndexView  # Or your specific view classes

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    
    # NEW: Explicit routes
    path('', IndexView.as_view(), name='home'),
    path('about/', IndexView.as_view(), name='about'),
    path('dashboard/', IndexView.as_view(), name='dashboard'),
    path('profile/', IndexView.as_view(), name='profile'),
    # ... add all your routes
    
    # OLD: Keep catch-all as fallback during testing
    re_path(r'^.*', IndexView.as_view(), name='catch-all'),
]
```

### Phase 2: Testing

- [ ] Test each explicit route individually
- [ ] Test that all routes return 200 status code
- [ ] Test that React Router handles client-side navigation
- [ ] Test browser refresh on each route
- [ ] Test direct URL navigation
- [ ] Test authentication/permissions on protected routes

**Testing checklist per route:**
```bash
# Test route exists
curl -I http://localhost:8000/your-route/

# Expected: HTTP/1.1 200 OK
```

### Phase 3: Monitor for Missing Routes

- [ ] Enable Django logging to catch 404s
- [ ] Monitor server logs for 404 errors
- [ ] Add any missing routes discovered
- [ ] Test again after adding new routes

**Enable 404 logging in `settings.py`:**
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
```

### Phase 4: Remove Catch-All

Once confident all routes are covered:

- [ ] Remove the catch-all route from `urls.py`
- [ ] Test that invalid routes now return proper 404
- [ ] Update documentation
- [ ] Commit changes

**Final `urls.py` (no catch-all):**
```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    
    # All explicit routes
    path('', IndexView.as_view(), name='home'),
    path('about/', IndexView.as_view(), name='about'),
    path('dashboard/', IndexView.as_view(), name='dashboard'),
    # ... all other routes
    
    # No catch-all route ✓
]
```

---

## ✅ Post-Migration Checklist

### Verify Functionality

- [ ] All defined routes work correctly
- [ ] Invalid routes return 404 (not the React app)
- [ ] React Router client-side navigation works
- [ ] Authentication/authorization works as expected
- [ ] All tests pass

### Update Documentation

- [ ] Add comments in `urls.py` linking to route configuration
- [ ] Update project README if necessary
- [ ] Document any custom view logic
- [ ] Update API documentation if affected

### Create Maintenance Process

- [ ] Document process for adding new routes
- [ ] Add comment blocks linking React and Django routes
- [ ] Consider creating management command to list routes
- [ ] Set up linter or pre-commit hook to check route sync

**Example comment in `urls.py`:**
```python
"""
REACT ROUTES - Keep in sync with frontend/src/routes.tsx

When adding a new React route:
1. Add the route to frontend/src/routes.tsx
2. Add corresponding path() to this file
3. Update core/routes_config.py if using centralized config
4. Test the route works in Django

Last updated: 2024-XX-XX
"""
```

---

## 🔧 Optional Enhancements

### Create Management Command

- [ ] Create `core/management/commands/list_routes.py`
- [ ] Add command to validate route configuration
- [ ] Add command to compare React and Django routes

**Example command:**
```python
# core/management/commands/list_routes.py
from django.core.management.base import BaseCommand
from core.routes_config import print_route_summary, validate_routes

class Command(BaseCommand):
    help = 'List all configured React routes and validate'

    def handle(self, *args, **options):
        if validate_routes():
            print_route_summary()
            self.stdout.write(self.style.SUCCESS('✓ Route configuration valid'))
        else:
            self.stdout.write(self.style.ERROR('✗ Route configuration has errors'))
```

### Generate Sitemap

- [ ] Create sitemap for explicit routes
- [ ] Add sitemap to robots.txt
- [ ] Submit sitemap to search engines

### Add Route Tests

- [ ] Create test file `core/tests/test_routes.py`
- [ ] Add test for each explicit route
- [ ] Add test verifying 404 for invalid routes
- [ ] Add to CI/CD pipeline

**Example tests:**
```python
from django.test import TestCase

class ExplicitRoutesTest(TestCase):
    def test_home_route(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_invalid_route_returns_404(self):
        response = self.client.get('/invalid-route-xyz/')
        self.assertEqual(response.status_code, 404)
```

---

## 🚨 Rollback Plan

If you need to rollback:

### Quick Rollback
```python
# In urls.py, simply add back the catch-all:
urlpatterns = [
    # ... existing routes
    re_path(r'^.*', IndexView.as_view(), name='index'),  # Add this back
]
```

### Full Rollback Steps

- [ ] Re-add catch-all route to `urls.py`
- [ ] Deploy updated code
- [ ] Verify application works
- [ ] Review what went wrong
- [ ] Plan fixes before trying again

---

## 📊 Benefits Checklist

After migration, you should have:

- [x] Better security (only defined routes accessible)
- [x] Proper 404 handling (invalid routes return correct status)
- [x] Self-documenting URLs (clear route structure)
- [x] SEO improvements (proper 404s, sitemap generation)
- [x] Route-specific logic (different auth/caching per route)
- [x] Production-ready routing (predictable behavior)

---

## 📚 Reference

- **Detailed Guide:** `docs/EXPLICIT_ROUTES.md`
- **Route Config Example:** `core/routes_config.py.example`
- **View Reference:** `docs/CBV_REFERENCE.md`
- **Deployment Guide:** `docs/DEPLOYMENT.md`

---

## 💡 Tips

1. **Start Small:** Migrate one section at a time (e.g., public routes first)
2. **Test Thoroughly:** Don't remove catch-all until you're confident
3. **Monitor Logs:** Watch for 404s during testing period
4. **Document Well:** Keep React and Django routes documented
5. **Automate Sync:** Consider tools to keep routes in sync
6. **Plan for Growth:** Use centralized config for easier maintenance

---

## ⏱️ Estimated Timeline

- **Small app** (< 10 routes): 1-2 hours
- **Medium app** (10-30 routes): 2-4 hours
- **Large app** (30+ routes): 4-8 hours

*Includes testing and documentation*

---

**Good luck with your migration! 🚀**

For questions or issues, refer to `docs/EXPLICIT_ROUTES.md` for detailed examples and patterns.