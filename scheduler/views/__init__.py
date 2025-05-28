# Import all views from the main module to maintain compatibility
from .main import (
    # Django REST Framework ViewSets
    CourseViewSet,
    StudentViewSet,
    SectionViewSet,
    ScheduleViewSet,
    SchedulerConfigViewSet,
    
    # Data management views
    clear_all_students,
    clear_all_courses,
    
    # Data import and export views
    import_courses,
    import_students,
    
    # Scheduler API endpoints
    run_scheduler,
    
    # Django template views
    index,
    courses,
    students,
    schedules,
    schedule_detail,
    compare_schedules,
    user_preferences,
    advanced_scheduler,
    save_preferences,
    run_scheduler_ui,
    
    # Ninja API endpoints
    list_courses,
    list_students,
    list_schedules,
    get_schedule,
    run_scheduler_api,
    
    # Error pages
    rate_limited_error
)

# Keep health view separate to avoid circular imports
from .health import health_check
