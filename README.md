# Django Scheduler Web Server

A production-ready web application for course scheduling, with an efficient implementation using Google OR-Tools optimization engine and a clean, modern interface built with Django.

## Features

### Core Features

- **Django Web Interface**: Modern, responsive user interface built with Bootstrap
- **REST API**: Complete API for programmatic access with OpenAPI documentation
- **Advanced Scheduling Algorithms**:
  - **Google OR-Tools Integration**: High-performance constraint satisfaction for optimized scheduling
  - **Rust Scheduler Interface**: Optional high-speed scheduling implementation
  - **Python Fallback**: Reliable alternative scheduling implementation
- **CSV Import/Export**: Easy data loading and result extraction
- **Admin Dashboard**: Full administrative control via Django admin
- **Multi-run Optimization**: Multiple algorithm runs with automatic selection of the optimal schedule

### Production-Ready Enhancements

- **User Authentication**: Secure login system with password management
- **Data Management**:
  - **Student Search**: Quickly find students by name, email, or grade
  - **Bulk Operations**: Clear all students, courses, etc. with confirmation
- **Performance Optimization**:
  - **Caching System**: Redis-based caching for frequently accessed data
  - **Asynchronous Processing**: Celery for background task processing
  - **Database Optimization**: Efficient query patterns with proper indexing
- **Monitoring & Reliability**:
  - **Performance Metrics**: Track and visualize system performance
  - **Sentry Integration**: Real-time error tracking and reporting
  - **Automated Backup**: Scheduled daily backups with retention policy
  - **Data Restoration**: Command-line tools for data recovery
- **DevOps Ready**:
  - **Docker Containerization**: Complete Docker and Docker Compose setup
  - **Nginx Configuration**: Production-grade web server setup
  - **CI/CD Support**: Automated testing framework
  - **Environment Separation**: Development/Production settings isolation
  - **Infrastructure as Code**: Complete deployment configuration

## System Requirements

- Python 3.8 or higher
- Database (SQLite by default, compatible with PostgreSQL, MySQL)

## Installation

1. Clone the repository:
```bash
git clone <repo-url>
cd schedulerwebserver
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the Python dependencies:
```bash
pip install -r requirements.txt
```

4. Run database migrations:
```bash
python manage.py migrate
```

5. Create a superuser for admin access:
```bash
python manage.py createsuperuser
```

6. Collect static files:
```bash
python manage.py collectstatic
```

## Running the Application

Start the development server:
```bash
python manage.py runserver
```

Access the application at http://127.0.0.1:8000/

## Data Format

### Course CSV Format

Courses can be imported from CSV with the following columns:
```
Name,MaxStudents,TimeSlot
Course1,25,AM
Course2,30,PM
Course3,20,FullDay
```

### Student CSV Format

Students can be imported from CSV with the following columns:
```
Email Address,Students First Name,Students Last Name,Grade in school this year,AM Course - 1st Choice. (Drop down option),AM Course - 2nd Choice. (Drop down option),...
```

## How the Scheduler Works

1. Students are grouped by priority (derived from their grade level)
2. Each priority group is shuffled to introduce randomness
3. Students are assigned to courses based on their preferences and course availability
4. The process repeats multiple times to find the optimal assignment
5. The schedule with the lowest "penalty score" (higher satisfaction) is selected as the best

## Architecture

The application has a clean, maintainable architecture:

- Django for the web interface, API, and data management
- A Python implementation of the original Go scheduler algorithm
- Multiple optimization runs to find the best possible schedule

## Project Structure

- `scheduler/` - Main Django application
  - `models.py` - Database models
  - `views.py` - Web and API endpoints
  - `scheduler_python.py` - Python implementation of the scheduler
  - `rust_interface.py` - Interface to the scheduler implementation
  - `templates/` - HTML templates
  - `static/` - CSS, JavaScript, and other static assets

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Original Go scheduler implementation by [agavris](https://github.com/agavris/june-academy-go)
- Rust bindings using PyO3 and Maturin
