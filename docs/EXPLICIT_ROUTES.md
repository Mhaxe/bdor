# Explicit Routes Pattern for React Integration

This document explains the **explicit routes pattern** for serving React applications with Django, as an alternative to the catch-all route approach.

## Overview

Instead of using a catch-all route (`re_path(r'^.*', IndexView.as_view())`), you explicitly define each React route in Django's URL configuration. This gives you better control, security, and clarity.

## Pattern Comparison

### Catch-All Route (Default Setup)

```python
# urls.py
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    re_path(r'^.*', IndexView.as_view(), name='index'),  # Matches everything
]
```

**Pros:**
- Simple to set up
- Automatically handles all React routes
- No need to update Django when adding React routes

**Cons:**
- Any invalid route returns the React app (not a proper 404)
- Less explicit about what routes exist
- Harder to apply route-specific logic

### Explicit Routes (Recommended for Production)

```python
# urls.py
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    
    # Explicitly defined React routes
    path('', IndexView.as_view(), name='home'),
    path('route-1/', IndexView.as_view(), name='route-1'),
    path('route-2/', IndexView.as_view(), name='route-2'),
    path('about/', IndexView.as_view(), name='about'),
    path('contact/', IndexView.as_view(), name='contact'),
]
```

**Pros:**
- Only defined routes are accessible
- Invalid routes properly return 404
- Self-documenting - URLs clearly show what exists
- Better security - no surprises
- SEO-friendly - search engines see proper 404s
- Can apply different logic per route

**Cons:**
- Must update Django URLs when adding React routes
- More verbose

## Implementation

### Basic Setup

```python
# balon_dor/urls.py
from django.contrib import admin
from django.urls import path, include

from core.views import IndexView

urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/v1/', include('api.urls')),
    
    # React application routes
    path('', IndexView.as_view(), name='home'),
    path('dashboard/', IndexView.as_view(), name='dashboard'),
    path('profile/', IndexView.as_view(), name='profile'),
    path('settings/', IndexView.as_view(), name='settings'),
    path('about/', IndexView.as_view(), name='about'),
    path('contact/', IndexView.as_view(), name='contact'),
]
```

### With Nested Routes

If your React app has nested routes like `/products/123` or `/users/profile/settings`:

```python
from django.urls import path, re_path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    
    # Top-level routes
    path('', IndexView.as_view(), name='home'),
    path('about/', IndexView.as_view(), name='about'),
    
    # Routes with dynamic segments
    re_path(r'^products/.*', IndexView.as_view(), name='products'),
    re_path(r'^users/.*', IndexView.as_view(), name='users'),
    re_path(r'^blog/.*', IndexView.as_view(), name='blog'),
]
```

This allows `/products/123`, `/products/categories/electronics`, etc., while still being more restrictive than a full catch-all.

## Advanced Patterns

### Different Views for Different Routes

You might want different Django views for different sections:

```python
# core/views.py
from django.views.generic import TemplateView


class IndexView(TemplateView):
    """Main application view"""
    template_name = "index.html"


class DashboardView(TemplateView):
    """Dashboard with authentication required"""
    template_name = "index.html"
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)


class PublicView(TemplateView):
    """Public pages with different cache settings"""
    template_name = "index.html"
```

```python
# urls.py
from core.views import IndexView, DashboardView, PublicView

urlpatterns = [
    # Public routes
    path('', PublicView.as_view(), name='home'),
    path('about/', PublicView.as_view(), name='about'),
    path('pricing/', PublicView.as_view(), name='pricing'),
    
    # Protected routes
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('profile/', DashboardView.as_view(), name='profile'),
    path('settings/', DashboardView.as_view(), name='settings'),
    
    # Admin routes
    path('admin/', admin.site.urls),
]
```

### Route-Specific Context Data

Pass different data to different routes:

```python
# core/views.py
class HomeView(TemplateView):
    template_name = "index.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Home - Balon d\'Or'
        context['meta_description'] = 'Welcome to Balon d\'Or'
        return context


class AboutView(TemplateView):
    template_name = "index.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'About Us - Balon d\'Or'
        context['meta_description'] = 'Learn more about our company'
        return context
```

```python
# urls.py
urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('about/', AboutView.as_view(), name='about'),
]
```

Then in your `index.html`:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>{{ page_title|default:"Balon d'Or" }}</title>
    <meta name="description" content="{{ meta_description|default:'Default description' }}" />
    <!-- rest of head -->
  </head>
  <body>
    <div id="root"></div>
  </body>
</html>
```

### Route Groups with Shared Logic

Group routes with common logic:

```python
# core/views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class BaseReactView(TemplateView):
    """Base view for all React routes"""
    template_name = "index.html"


class PublicReactView(BaseReactView):
    """Public routes - cached"""
    
    @method_decorator(cache_page(60 * 15))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class PrivateReactView(LoginRequiredMixin, BaseReactView):
    """Private routes - require authentication"""
    login_url = '/login/'


class AdminReactView(PermissionRequiredMixin, BaseReactView):
    """Admin routes - require admin permission"""
    permission_required = 'auth.is_staff'
```

## Managing Routes Sync Between React and Django

### Option 1: Centralized Route Configuration

Create a shared route configuration:

```python
# core/routes.py
"""
Centralized route configuration.
Keep this in sync with React Router routes in frontend/src/routes.tsx
"""

PUBLIC_ROUTES = [
    ('', 'home'),
    ('about/', 'about'),
    ('pricing/', 'pricing'),
    ('contact/', 'contact'),
]

AUTHENTICATED_ROUTES = [
    ('dashboard/', 'dashboard'),
    ('profile/', 'profile'),
    ('settings/', 'settings'),
]

DYNAMIC_ROUTES = [
    (r'^blog/.*', 'blog'),
    (r'^products/.*', 'products'),
    (r'^users/.*', 'users'),
]
```

```python
# urls.py
from django.urls import path, re_path
from core.views import PublicReactView, PrivateReactView
from core.routes import PUBLIC_ROUTES, AUTHENTICATED_ROUTES, DYNAMIC_ROUTES

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
]

# Add public routes
for route, name in PUBLIC_ROUTES:
    urlpatterns.append(path(route, PublicReactView.as_view(), name=name))

# Add authenticated routes
for route, name in AUTHENTICATED_ROUTES:
    urlpatterns.append(path(route, PrivateReactView.as_view(), name=name))

# Add dynamic routes
for pattern, name in DYNAMIC_ROUTES:
    urlpatterns.append(re_path(pattern, PublicReactView.as_view(), name=name))
```

### Option 2: Management Command to Generate URLs

Create a management command that reads React Router config:

```python
# core/management/commands/sync_routes.py
from django.core.management.base import BaseCommand
import json
import os

class Command(BaseCommand):
    help = 'Sync React routes to Django URL configuration'
    
    def handle(self, *args, **options):
        # Read React routes from a JSON file
        routes_file = 'frontend/src/routes.json'
        with open(routes_file, 'r') as f:
            routes = json.load(f)
        
        # Generate urls.py snippet
        self.stdout.write('Add these routes to your urls.py:')
        for route in routes:
            path_str = f"path('{route['path']}/', IndexView.as_view(), name='{route['name']}'),"
            self.stdout.write(path_str)
```

### Option 3: Comments in Both Files

Keep a comment block in both files:

```python
# urls.py
"""
REACT ROUTES - Keep in sync with frontend/src/routes.tsx

Current routes:
- / (home)
- /dashboard
- /profile
- /settings
- /about
- /contact
- /products/* (dynamic)
- /blog/* (dynamic)

Last updated: 2024-01-15
"""

urlpatterns = [
    # ... route definitions
]
```

```typescript
// frontend/src/routes.tsx
/**
 * REACT ROUTES - Keep in sync with balon_dor/urls.py
 * 
 * Current routes:
 * - / (home)
 * - /dashboard
 * - /profile
 * - /settings
 * - /about
 * - /contact
 * - /products/:id (dynamic)
 * - /blog/:slug (dynamic)
 * 
 * Last updated: 2024-01-15
 */
```

## Testing Explicit Routes

```python
# core/tests.py
from django.test import TestCase, Client
from django.urls import reverse


class ExplicitRoutesTest(TestCase):
    def setUp(self):
        self.client = Client()
    
    def test_home_route_exists(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_dashboard_route_exists(self):
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)
    
    def test_invalid_route_returns_404(self):
        """This is the key benefit - invalid routes return proper 404"""
        response = self.client.get('/nonexistent-route/')
        self.assertEqual(response.status_code, 404)
    
    def test_all_routes_use_correct_template(self):
        routes = ['/', '/dashboard/', '/about/']
        for route in routes:
            response = self.client.get(route)
            self.assertTemplateUsed(response, 'index.html')
```

## Migration Strategy

### Step 1: Document Current React Routes

List all routes in your React app:

```bash
# In your React project
grep -r "path=" frontend/src/ | grep -o 'path="[^"]*"'
```

### Step 2: Add Explicit Routes Alongside Catch-All

```python
# urls.py
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    
    # Explicit routes (new)
    path('', IndexView.as_view(), name='home'),
    path('dashboard/', IndexView.as_view(), name='dashboard'),
    path('profile/', IndexView.as_view(), name='profile'),
    
    # Keep catch-all for now as fallback
    re_path(r'^.*', IndexView.as_view(), name='catch-all'),
]
```

### Step 3: Test and Monitor

- Test all routes work correctly
- Monitor 404 logs to find any missed routes
- Add any missing routes

### Step 4: Remove Catch-All

Once confident all routes are covered:

```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    
    # All explicit routes
    path('', IndexView.as_view(), name='home'),
    path('dashboard/', IndexView.as_view(), name='dashboard'),
    path('profile/', IndexView.as_view(), name='profile'),
    # ... all other routes
    
    # Catch-all removed ✓
]
```

## Best Practices

1. **Use trailing slashes consistently** - Django convention is to use them
2. **Name your routes** - Makes them referenceable in Django templates
3. **Group related routes** - Keep routes organized by feature/section
4. **Document route purposes** - Add comments explaining route groups
5. **Keep routes in sync** - Use one of the sync strategies above
6. **Test invalid routes** - Ensure they return proper 404s
7. **Consider SEO** - Explicit routes help with sitemap generation

## Generating a Sitemap

With explicit routes, generating a sitemap is straightforward:

```python
# core/sitemaps.py
from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        return ['home', 'about', 'contact', 'pricing']

    def location(self, item):
        return reverse(item)
```

```python
# urls.py
from django.contrib.sitemaps.views import sitemap
from core.sitemaps import StaticViewSitemap

sitemaps = {
    'static': StaticViewSitemap,
}

urlpatterns = [
    # ... other routes
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
]
```

## Conclusion

The explicit routes pattern provides:

✅ **Better security** - Only defined routes work  
✅ **Proper 404 handling** - Invalid routes return correct errors  
✅ **Self-documentation** - URLs clearly show app structure  
✅ **SEO benefits** - Better control over indexable pages  
✅ **Route-specific logic** - Different views/auth per route  
✅ **Production readiness** - More predictable behavior  

While it requires keeping Django and React routes in sync, the benefits for production applications make it worthwhile, especially for applications with a defined set of routes rather than user-generated or dynamic content.

---

**When to use explicit routes:**
- Production applications
- Apps with security requirements
- Apps with defined route structures
- When you need route-specific logic
- When proper 404s matter (SEO, UX)

**When to use catch-all:**
- Early development/prototyping
- Apps with many dynamic routes
- When rapid iteration is priority
- Internal tools with less security concern