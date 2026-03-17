# Balon d'Or - Full Stack Application
# trigger
A full-stack web application built with Django (backend) and React + Vite + TypeScript (frontend).

## 🏗️ Architecture

This project uses a **single-server deployment** where Django serves:
- Pre-built React frontend (SPA)
- Django admin interface
- API endpoints

## 📁 Project Structure

```
balon-dor/
├── balon_dor/           # Django project configuration
│   ├── settings.py      # Django settings (configured for React)
│   ├── urls.py          # URL routing with React catch-all
│   └── wsgi.py          # WSGI application entry point
├── core/                # Django app for frontend views
│   └── views.py         # Serves React index.html
├── frontend/            # React + Vite + TypeScript
│   ├── src/             # React source code
│   ├── dist/            # Production build (generated)
│   └── package.json     # Frontend dependencies
├── docs/                # Documentation
│   └── DEPLOYMENT.md    # Detailed deployment guide
├── manage.py            # Django management script
└── requirements.txt     # Python dependencies
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Bun (JavaScript runtime and package manager)
- pip and virtualenv

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd balon-dor
   ```

2. **Set up Python virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install frontend dependencies**
   ```bash
   cd frontend
   bun install
   cd ..
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

## 💻 Development

### Option 1: Develop with Separate Servers (Recommended for Development)

**Terminal 1 - Frontend (with hot reload):**
```bash
cd frontend
bun run dev
```
Frontend runs at: `http://localhost:5173`

**Terminal 2 - Backend:**
```bash
python manage.py runserver
```
Backend runs at: `http://localhost:8000`

### Option 2: Develop with Single Server (Test Production Setup)

1. **Build React frontend:**
   ```bash
   cd frontend
   bun run build
   cd ..
   ```

2. **Run Django server:**
   ```bash
   python manage.py runserver
   ```

Access everything at: `http://localhost:8000`

## 🔧 Available Commands

### Frontend (run in `frontend/` directory)

```bash
bun run dev       # Start Vite dev server with HMR
bun run build     # Build for production
bun run preview   # Preview production build locally
bun run lint      # Run ESLint
```

### Backend (run in project root)

```bash
python manage.py runserver          # Start development server
python manage.py makemigrations     # Create new migrations
python manage.py migrate            # Apply migrations
python manage.py createsuperuser    # Create admin user
python manage.py collectstatic      # Collect static files (production)
python manage.py check              # Check for issues
```

## 🌐 URL Structure

When running the integrated Django server:

- `/` - React SPA (all client-side routes)
- `/admin/` - Django admin interface
- `/api/` - API endpoints (when implemented)

The catch-all route ensures React Router handles client-side navigation.

### Alternative: Explicit Routes (Recommended for Production)

For better security and control, you can switch from catch-all to explicit routes:

```python
# Instead of catch-all: re_path(r'^.*', IndexView.as_view())
# Use explicit routes:
path('', IndexView.as_view(), name='home'),
path('route-1/', IndexView.as_view(), name='route-1'),
path('route-2/', IndexView.as_view(), name='route-2'),
```

**Benefits:** Better security, proper 404 handling, self-documenting URLs. See `docs/EXPLICIT_ROUTES.md` for details.

## 📦 Building for Production

1. **Build the React frontend:**
   ```bash
   cd frontend
   bun run build
   ```

2. **Collect static files:**
   ```bash
   python manage.py collectstatic --noinput
   ```

3. **Set production settings:**
   - Set `DEBUG = False`
   - Configure `ALLOWED_HOSTS`
   - Set up proper `SECRET_KEY`
   - Configure database (if not using SQLite)

4. **Run with production server:**
   ```bash
   gunicorn balon_dor.wsgi:application --bind 0.0.0.0:8000
   ```

For detailed production deployment instructions, see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

## 🛠️ Technology Stack

### Backend
- **Django 5.1.4** - Web framework
- **Python 3.x** - Programming language
- **SQLite** - Database (development)

### Frontend
- **React 19** - UI library
- **TypeScript** - Type-safe JavaScript
- **Vite 7** - Build tool and dev server
- **React Router 7** - Client-side routing
- **Bun** - JavaScript runtime and package manager

## 📚 Documentation

- [DEPLOYMENT.md](docs/DEPLOYMENT.md) - Comprehensive deployment guide
- [EXPLICIT_ROUTES.md](docs/EXPLICIT_ROUTES.md) - Explicit routes pattern (recommended for production)
- [CBV_REFERENCE.md](docs/CBV_REFERENCE.md) - Class-based view reference and extensions
- [Django Documentation](https://docs.djangoproject.com/)
- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vitejs.dev/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 Notes

- The React app is served by Django in production
- All React routes are handled by the catch-all URL pattern
- Static files from React build are served via Django's static files system
- API endpoints should be added before the catch-all route in `urls.py`

## ⚠️ Common Issues

**Static files not loading?**
- Rebuild React: `cd frontend && bun run build`
- Check `STATICFILES_DIRS` in `settings.py`

**React routes showing 404?**
- Ensure catch-all route is last in `urls.py`

**Changes not reflecting?**
- Clear browser cache (Ctrl+Shift+R)
- Rebuild React frontend
- Restart Django server

## 📄 License

[Add your license here]

## 👥 Authors

[Add authors here]