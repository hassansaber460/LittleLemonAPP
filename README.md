# LittleLemonAPP

A Django-based web application built with Django REST Framework. This project is part of my backend development journey, focusing on building RESTful APIs and implementing Django best practices.

## 🚀 Technologies

- **Python** – Backend programming language
- **Django** – Web framework
- **Django REST Framework** – RESTful API development
- **Pipenv** – Dependency and virtual environment management
- **MySQL / SQLite** – Database management
- **Django Debug Toolbar** – Development and debugging

## 📋 Prerequisites

Before getting started, make sure you have installed:

- [Python](https://www.python.org/downloads/)
- [Pipenv](https://pipenv.pypa.io/en/latest/)
- [Git](https://git-scm.com/)

## ⚙️ Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/hassansaber460/LittleLemonAPP.git
```

Navigate to the project directory:

```bash
cd LittleLemonAPP
```

### 2. Install Dependencies

Install Pipenv if it is not already installed:

```bash
pip install pipenv
```

Install the project dependencies:

```bash
pipenv install
```

Activate the virtual environment:

```bash
pipenv shell
```

### 3. Install Django REST Framework

Install Django REST Framework:

```bash
pipenv install djangorestframework
```

Add `rest_framework` to `INSTALLED_APPS` in your Django `settings.py`:

```python
INSTALLED_APPS = [
    # Other installed applications
    "rest_framework",
]
```

📚 **Documentation:** [Django REST Framework](https://www.django-rest-framework.org/)

### 4. Install Django Debug Toolbar

Install Django Debug Toolbar:

```bash
pipenv install django-debug-toolbar
```

Add `debug_toolbar` to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # Other installed applications
    "debug_toolbar",
]
```

Add the Debug Toolbar middleware to `MIDDLEWARE`:

```python
MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    # Other middleware
]
```

Configure `INTERNAL_IPS` in `settings.py`:

```python
INTERNAL_IPS = [
    "127.0.0.1",
]
```

Add the Debug Toolbar URL configuration to your project's `urls.py`:

```python
from django.urls import include, path

urlpatterns = [
    # Other URL patterns
    path("__debug__/", include("debug_toolbar.urls")),
]
```

📚 **Documentation:** [Django Debug Toolbar](https://django-debug-toolbar.readthedocs.io/en/latest/)

### 5. Apply Database Migrations

```bash
python manage.py migrate
```

### 6. Run the Development Server

```bash
python manage.py runserver
```

The application will be available at:

[http://127.0.0.1:8000/](http://127.0.0.1:8000/)

## 📖 Useful Resources

| Resource | Documentation |
|---|---|
| Django | [Official Documentation](https://docs.djangoproject.com/en/5.2/) |
| Django REST Framework | [Official Documentation](https://www.django-rest-framework.org/) |
| Django Debug Toolbar | [Official Documentation](https://django-debug-toolbar.readthedocs.io/en/latest/) |
| Pipenv | [Official Documentation](https://pipenv.pypa.io/en/latest/) |
| Python | [Official Documentation](https://docs.python.org/3/) |

## 👨‍💻 Author

**Hassan Saber**

- GitHub: [@hassansaber460](https://github.com/hassansaber460)

---

⭐ If you find this project useful, feel free to star the repository!
