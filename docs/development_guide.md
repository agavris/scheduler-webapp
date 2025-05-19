# Development Guide

This document provides guidelines for developing and maintaining the Django Scheduler Web Server.

## Project Structure

```
schedulerwebserver/
├── backups/                  # Database backups
├── docs/                     # Documentation
├── scheduler/                # Main application
│   ├── admin.py              # Admin interface
│   ├── models.py             # Database models
│   ├── ortools_scheduler.py  # OR-Tools scheduler implementation
│   ├── rust_interface.py     # Rust integration interface
│   ├── scheduler_python.py   # Python fallback scheduler
│   ├── serializers.py        # REST API serializers
│   ├── templates/            # HTML templates
│   ├── urls.py               # URL routing
│   └── views.py              # View controllers
├── scheduler_project/        # Project settings
│   ├── settings.py           # Main settings file
│   ├── settings_prod.py      # Production settings
│   ├── urls.py               # Project URL routing
│   └── wsgi.py               # WSGI entry point
├── docker-compose.yml        # Docker configuration
├── docker-compose-dev.yml    # Development Docker configuration
├── Dockerfile                # Docker build instructions
├── requirements.txt          # Python dependencies
└── run-scheduler.sh          # Convenience script
```

## Core Components

### 1. Models

The core models in `models.py` include:

- `Course`: Represents a course offering with name, time slot, and max students
- `Student`: Represents a student with preferences and assigned courses
- `Section`: Represents a section of a course with enrolled students
- `Schedule`: Represents a complete scheduling solution
- `ScheduleSnapshot`: Captures student assignments at a point in time

### 2. Scheduler Implementations

- `ortools_scheduler.py`: Main scheduler using Google OR-Tools
- `scheduler_python.py`: Python fallback implementation
- `rust_interface.py`: Interface to optional Rust implementation

### 3. Views and APIs

- REST API endpoints in `views.py`
- Django template views for web interface
- Ninja API for additional endpoints

## Satisfaction Score Calculation

The schedule quality is measured by a satisfaction score:

1. Each student receives a score between 0.0 and 1.0
   - Lower scores indicate better satisfaction (0.0 is perfect)
   - Higher scores indicate worse satisfaction (1.0 is worst)

2. The score is calculated based on the position of assigned courses in preference lists
   - Top preferences get lower scores
   - Less preferred or non-preferred get higher scores

3. The total schedule score is the average of all student scores
   - Lower overall scores indicate better schedules
   - Optimal schedule has the lowest score possible

## Development Workflow

### Local Development

1. Set up the virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Run migrations:
   ```bash
   python manage.py migrate
   ```

3. Start the development server:
   ```bash
   python manage.py runserver 8080
   ```

### Docker Development

1. Start all services:
   ```bash
   ./run-scheduler.sh start
   ```

2. View logs:
   ```bash
   ./run-scheduler.sh logs
   ```

3. Stop all services:
   ```bash
   ./run-scheduler.sh stop
   ```

## Adding New Features

When adding new features, follow these steps:

1. **Create models** - Add new models to `models.py` if needed
2. **Create migrations** - Run `python manage.py makemigrations`
3. **Create serializers** - Add serializers for new models in `serializers.py`
4. **Add API endpoints** - Implement API endpoints in `views.py`
5. **Add UI components** - Add templates and update frontend as needed
6. **Write tests** - Add tests for new functionality
7. **Document changes** - Update documentation in `docs/`

## Scheduler Algorithm Modifications

When modifying the scheduling algorithm:

1. Make changes to `ortools_scheduler.py` for the main implementation
2. Maintain compatibility in `scheduler_python.py` for the fallback
3. Keep scoring consistent with the satisfaction score method in the Student model
4. Test with various preference scenarios to ensure optimal schedules

## Best Practices

- Keep the satisfaction score calculation consistent throughout the application
- Use Django REST Framework for API endpoints
- Follow PEP 8 style guide for Python code
- Document all functions and classes with docstrings
- Add new settings to `settings.py` and environment-specific overrides
- Version control database schema changes through migrations
