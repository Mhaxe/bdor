# Class-Based View Reference

This document provides a quick reference for the class-based view implementation used to serve the React frontend.

## Current Implementation

### `core/views.py`

```python
from django.views.generic import TemplateView


class IndexView(TemplateView):
    """
    Serves the main index.html file of the React application.
    This view acts as the entry point for the React SPA.
    """
    template_name = "index.html"
```

### `balon_dor/urls.py`

```python
from django.contrib import admin
from django.urls import path, re_path

from core.views import IndexView

urlpatterns = [
    path("admin/", admin.site.urls),
    # Add your API routes here before the catch-all route
    # path('api/', include('your_api.urls')),
    
    # Catch-all route for React frontend - MUST be last
    re_path(r"^.*", IndexView.as_view(), name="index"),
]
```

## Why TemplateView?

`TemplateView` is perfect for this use case because:

✅ **Simple and declarative** - Just set `template_name`  
✅ **Built-in rendering** - Handles template rendering automatically  
✅ **Extensible** - Easy to add context data or custom logic  
✅ **Standard Django** - Follows Django best practices  

## Extending the View

### Adding Context Data

If you need to pass data to the template (e.g., for SEO meta tags or initial state):

```python
from django.views.generic import TemplateView


class IndexView(TemplateView):
    template_name = "index.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_name'] = 'Balon d\'Or'
        context['meta_description'] = 'Your site description'
        return context
```

### Adding Custom Headers

```python
from django.views.generic import TemplateView


class IndexView(TemplateView):
    template_name = "index.html"
    
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        response['X-Frame-Options'] = 'DENY'
        response['X-Content-Type-Options'] = 'nosniff'
        return response
```

### Checking Authentication

If you want to require authentication for the entire SPA:

```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = "index.html"
    login_url = '/admin/login/'  # Or your custom login URL
```

### Caching the View

For production, you might want to cache the view:

```python
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView


@method_decorator(cache_page(60 * 15), name='dispatch')  # Cache for 15 minutes
class IndexView(TemplateView):
    template_name = "index.html"
```

## Alternative: RedirectView for API-Only Backend

If your Django backend only serves APIs and you want to redirect to a separate frontend:

```python
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    re_path(r'^.*', RedirectView.as_view(url='https://your-frontend-domain.com/', permanent=False)),
]
```

## Common Patterns

### Multiple React Apps

If you have multiple React SPAs in different routes:

```python
# views.py
from django.views.generic import TemplateView


class MainAppView(TemplateView):
    template_name = "main/index.html"


class AdminDashboardView(TemplateView):
    template_name = "admin_dashboard/index.html"


# urls.py
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    re_path(r'^dashboard/.*', AdminDashboardView.as_view()),
    re_path(r'^.*', MainAppView.as_view()),  # Main app catch-all
]
```

### Adding Rate Limiting

Using django-ratelimit:

```python
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from django.views.generic import TemplateView


@method_decorator(ratelimit(key='ip', rate='100/h'), name='dispatch')
class IndexView(TemplateView):
    template_name = "index.html"
```

## Testing the View

### Unit Test

```python
from django.test import TestCase, Client
from django.urls import reverse


class IndexViewTest(TestCase):
    def setUp(self):
        self.client = Client()
    
    def test_index_view_returns_200(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_index_view_uses_correct_template(self):
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'index.html')
    
    def test_catch_all_route_works(self):
        # Test that React Router routes return the same template
        response = self.client.get('/about')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')
```

## Performance Tips

1. **Enable gzip compression** in your production server (Nginx/Apache)
2. **Use caching** for the index view (see example above)
3. **Set proper cache headers** for static assets
4. **Use a CDN** for serving static files in production

## Best Practices

✅ Keep the view simple - it's just serving a template  
✅ Add API routes before the catch-all  
✅ Use mixins for authentication, permissions, etc.  
✅ Cache the view in production  
✅ Let React handle client-side routing  
✅ Use Django for API, auth, and server-side logic  

## Related Documentation

- [Django TemplateView](https://docs.djangoproject.com/en/stable/ref/class-based-views/base/#templateview)
- [Django Class-Based Views](https://docs.djangoproject.com/en/stable/topics/class-based-views/)
- [Mixins](https://docs.djangoproject.com/en/stable/topics/class-based-views/mixins/)

## Explicit Routes vs Catch-All

### Current Setup (Catch-All)

```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    re_path(r'^.*', IndexView.as_view(), name='index'),  # Matches everything
]
```

### Alternative: Explicit Routes (Recommended for Production)

Instead of using a catch-all route, explicitly define each React route:

```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    
    # Explicitly define each React route
    path('', IndexView.as_view(), name='home'),
    path('route-1/', IndexView.as_view(), name='route-1'),
    path('route-2/', IndexView.as_view(), name='route-2'),
    path('dashboard/', IndexView.as_view(), name='dashboard'),
    path('about/', IndexView.as_view(), name='about'),
    # No catch-all - invalid routes return proper 404
]
```

**Benefits:**
- ✅ Better security - only defined routes are accessible
- ✅ Proper 404 handling - invalid routes return correct errors
- ✅ Self-documenting - URLs clearly show app structure
- ✅ SEO-friendly - search engines see proper 404s
- ✅ Route-specific logic - can apply different auth/caching per route

**For nested routes:**

```python
urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Specific top-level routes
    path('', IndexView.as_view(), name='home'),
    path('about/', IndexView.as_view(), name='about'),
    
    # Pattern matching for sections with nested routes
    re_path(r'^products/.*', IndexView.as_view(), name='products'),
    re_path(r'^blog/.*', IndexView.as_view(), name='blog'),
]
```

See `docs/EXPLICIT_ROUTES.md` for comprehensive guidance on this pattern.

---

**Note:** This implementation is production-ready and follows Django best practices for serving SPAs.