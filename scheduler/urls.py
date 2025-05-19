from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Set up DRF router
router = DefaultRouter()
router.register(r'courses', views.CourseViewSet)
router.register(r'students', views.StudentViewSet)
router.register(r'sections', views.SectionViewSet)
router.register(r'schedules', views.ScheduleViewSet)
router.register(r'configs', views.SchedulerConfigViewSet)

urlpatterns = [
    # API endpoints
    path('api/', include((router.urls, 'api'), namespace='api')),
    path('api/import/courses/', views.import_courses, name='import_courses'),
    path('api/import/students/', views.import_students, name='import_students'),
    path('api/run-scheduler/', views.run_scheduler, name='api_run_scheduler'),
    path('api/clear-all-students/', views.clear_all_students, name='clear_all_students'),
    path('api/clear-all-courses/', views.clear_all_courses, name='clear_all_courses'),
    
    # Web UI paths
    path('', views.index, name='index'),
    path('courses/', views.courses, name='courses'),
    path('students/', views.students, name='students'),
    path('schedules/', views.schedules, name='schedules'),
    path('schedules/<int:pk>/', views.schedule_detail, name='schedule_detail'),
    path('compare-schedules/', views.compare_schedules, name='compare_schedules'),
    path('run-scheduler/', views.run_scheduler_ui, name='run_scheduler_ui'),
    path('advanced-scheduler/', views.advanced_scheduler, name='advanced_scheduler'),
    path('preferences/', views.user_preferences, name='user_preferences'),
    path('api/save-preferences/', views.save_preferences, name='save_preferences'),
]

# Include Ninja API
urlpatterns += [path('ninja-api/', views.api.urls)]
