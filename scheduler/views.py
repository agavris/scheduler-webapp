from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import JsonResponse
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.views import APIView

import json
import csv
import io
import pandas as pd
import logging
import os
from datetime import datetime
from typing import List, Dict, Optional

from ninja import NinjaAPI

from .models import Course, Student, Section, Schedule, ScheduleSnapshot, SchedulerConfig, UserPreference
from .serializers import (
    CourseSerializer, StudentSerializer, SectionSerializer,
    ScheduleSerializer, ScheduleSnapshotSerializer, SchedulerConfigSerializer,
    RequestSerializer
)
from .rust_interface import RustSchedulerInterface
from .scheduler_python import PythonScheduler

logger = logging.getLogger(__name__)

# Create Ninja API instance
api = NinjaAPI()

# Registration View
def register(request):
    """Handle user registration"""
    if request.user.is_authenticated:
        return redirect('index')
        
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create default preferences for the new user
            UserPreference.objects.create(user=user)
            messages.success(request, 'Account created successfully! You can now log in.')
            return redirect('login')
    else:
        form = UserCreationForm()
    
    return render(request, 'scheduler/register.html', {'form': form})

# Django REST Framework ViewSets
class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    
    @action(detail=False, methods=['get'])
    def with_preferences(self, request):
        """Return all students with their preferences and course assignments"""
        students = self.get_queryset()
        data = []
        
        for student in students:
            student_data = {
                'id': student.id,
                'first_name': student.first_name,
                'last_name': student.last_name,
                'priority': student.priority,
                'am_preferences': student.get_am_preferences(),
                'pm_preferences': student.get_pm_preferences(),
                'am_course': student.am_course.name if student.am_course else None,
                'pm_course': student.pm_course.name if student.pm_course else None,
                'full_day_course': student.full_day_course.name if student.full_day_course else None
            }
            data.append(student_data)
            
        return Response(data)

class SectionViewSet(viewsets.ModelViewSet):
    queryset = Section.objects.all()
    serializer_class = SectionSerializer

class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    
    @action(detail=False, methods=['post'])
    @login_required
    def clear_old_schedules(self, request):
        """Delete all schedules that aren't marked as 'best'"""
        # Keep the best schedule
        best_schedule = Schedule.objects.filter(is_best=True).first()
        
        # Delete all other schedules
        deleted_count = 0
        if best_schedule:
            deleted_count = Schedule.objects.exclude(id=best_schedule.id).count()
            Schedule.objects.exclude(id=best_schedule.id).delete()
        else:
            deleted_count = Schedule.objects.all().count()
            Schedule.objects.all().delete()
        
        return Response({
            'message': f'Successfully deleted {deleted_count} old schedules.',
            'remaining': Schedule.objects.count()
        })
    
    @action(detail=True, methods=['get'])
    def export_csv(self, request, pk=None):
        """Export a schedule to CSV format"""
        schedule = self.get_object()
        
        # Create in-memory text streams for results and sections CSVs
        results_output = io.StringIO()
        sections_output = io.StringIO()
        
        # Create CSV writers
        results_writer = csv.writer(results_output)
        sections_writer = csv.writer(sections_output)
        
        # Write headers
        results_writer.writerow([
            'Email', 'First Name', 'Last Name', 'Grade',
            'AM Course', 'PM Course', 'FD Course', 'Satisfaction Score'
        ])
        sections_writer.writerow([
            'Course Name', 'Max Students', 'Enrolled Students', 'Student Roster'
        ])
        
        # Write student data
        snapshots = schedule.snapshots.all().select_related('student', 'am_course', 'pm_course', 'full_day_course')
        for snapshot in snapshots:
            student = snapshot.student
            results_writer.writerow([
                student.email,
                student.first_name,
                student.last_name,
                student.grade,
                snapshot.am_course.name if snapshot.am_course else '',
                snapshot.pm_course.name if snapshot.pm_course else '',
                snapshot.full_day_course.name if snapshot.full_day_course else '',
                snapshot.satisfaction_score
            ])
        
        # Write section data
        sections = Section.objects.all().select_related('course')
        for section in sections:
            students = section.get_students()
            student_names = ', '.join([f"{s.first_name} {s.last_name}" for s in students])
            sections_writer.writerow([
                section.course.name,
                section.max_students,
                section.enrolled_students_count,
                student_names
            ])
        
        # Create response with the CSVs as attachments
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="results_{timestamp}.csv"'
        response.write(results_output.getvalue())
        
        return response

class SchedulerConfigViewSet(viewsets.ModelViewSet):
    queryset = SchedulerConfig.objects.all()
    serializer_class = SchedulerConfigSerializer

# Data management views
@api_view(['DELETE'])
@csrf_exempt
def clear_all_students(request):
    """Clear all students from the database"""
    try:
        # Delete all student records
        count = Student.objects.count()
        Student.objects.all().delete()
        
        # Clear all sections (remove student enrollments)
        for section in Section.objects.all():
            section.clear_students()
        
        return Response({'message': f'Successfully deleted {count} students'}, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error clearing students: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@csrf_exempt
def clear_all_courses(request):
    """Clear all courses from the database"""
    try:
        # Delete all course records
        count = Course.objects.count()
        Course.objects.all().delete()
        
        return Response({'message': f'Successfully deleted {count} courses'}, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error clearing courses: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Data import and export views
@api_view(['POST'])
@csrf_exempt
def import_courses(request):
    """Import courses from a CSV file"""
    if 'file' not in request.FILES:
        return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
    file = request.FILES['file']
    
    try:
        df = pd.read_csv(file)
        required_columns = ['Name', 'MaxStudents', 'TimeSlot']
        
        # Check if required columns exist
        for col in required_columns:
            if col not in df.columns:
                return Response({'error': f'Column {col} is missing'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Process and save courses
        for _, row in df.iterrows():
            course, created = Course.objects.update_or_create(
                name=row['Name'],
                defaults={
                    'max_students': row['MaxStudents'],
                    'time_slot': row['TimeSlot']
                }
            )
            
            # Create a section for this course if it doesn't exist
            if not hasattr(course, 'section'):
                Section.objects.create(course=course)
        
        return Response({'message': f'Successfully imported {len(df)} courses'}, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        logger.error(f"Error importing courses: {e}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@csrf_exempt
def import_students(request):
    """Import students and their course preferences from a CSV file"""
    if 'file' not in request.FILES:
        return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
    file = request.FILES['file']
    
    try:
        df = pd.read_csv(file)
        required_columns = ['Email Address', 'Students First Name', 'Students Last Name', 'Grade in school this year']
        
        # Check if required columns exist
        for col in required_columns:
            if col not in df.columns:
                return Response({'error': f'Column {col} is missing'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Process and save students
        priority_map = {'Freshman': 3, 'Sophomore': 2, 'Junior': 1}
        
        for _, row in df.iterrows():
            # Extract basic student information
            email = row['Email Address']
            first_name = row['Students First Name']
            last_name = row['Students Last Name']
            grade = row['Grade in school this year']
            priority = priority_map.get(grade, 3)  # Default to lowest priority if grade not recognized
            
            # Extract course preferences
            am_preferences = [
                row.get('AM Course - 1st Choice. (Drop down option)', ''),
                row.get('AM Course - 2nd Choice. (Drop down option)', ''),
                row.get('AM Course - 3rd Choice. (Drop down option)', ''),
                row.get('AM Course - 4th Choice. (Drop down option)', ''),
                row.get('AM Course - 5th Choice. (Drop down option)', '')
            ]
            am_preferences = [p for p in am_preferences if p]  # Remove empty preferences
            
            pm_preferences = [
                row.get('PM Course - 1st Choice. (Drop down option)', ''),
                row.get('PM Course - 2nd Choice. (Drop down option)', ''),
                row.get('PM Course - 3rd Choice. (Drop down option)', ''),
                row.get('PM Course - 4th Choice. (Drop down option)', ''),
                row.get('PM Course - 5th Choice. (Drop down option)', '')
            ]
            pm_preferences = [p for p in pm_preferences if p]  # Remove empty preferences
            
            # Create or update student
            student, created = Student.objects.update_or_create(
                email=email,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'grade': grade,
                    'priority': priority,
                    'am_preferences': am_preferences,
                    'pm_preferences': pm_preferences
                }
            )
        
        return Response({'message': f'Successfully imported {len(df)} students'}, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        logger.error(f"Error importing students: {e}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# Scheduler API endpoints
@api_view(['POST'])
@csrf_exempt
def run_scheduler(request):
    """Run the scheduler algorithm with the given configuration"""
    try:
        # Parse configuration
        config_data = request.data.get('config', {})
        iterations = config_data.get('iterations', 1000)
        min_course_fill = config_data.get('min_course_fill', 0.75)
        early_stop_score = config_data.get('early_stop_score', 0.0)
        multiple_runs = config_data.get('multiple_runs', False)  # New option for multiple runs
        priority_weight = config_data.get('priority_weight', 'standard')  # Priority weighting option
        run_count = config_data.get('run_count', 3) if multiple_runs else 1  # Number of runs to try
        
        # Create a config record for tracking
        config = SchedulerConfig.objects.create(
            name=f"Run_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            iterations=iterations,
            min_course_fill=min_course_fill,
            early_stop_score=early_stop_score
        )
        
        # Get all courses and students
        courses = Course.objects.all()
        students = Student.objects.all()
        
        if not courses or not students:
            return Response(
                {'error': 'Cannot run scheduler without courses and students'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Initialize the Rust scheduler interface
        scheduler_interface = RustSchedulerInterface()
        
        # Set up configuration with additional options
        scheduler_config = {
            'iterations': iterations,
            'min_course_fill': min_course_fill,
            'early_stop_score': early_stop_score,
            'priority_weight': priority_weight  # Pass the priority weight option
        }
        
        # If multiple runs requested, run the scheduler multiple times and pick the best result
        best_result = None
        best_score = float('inf')  # Lower is better
        
        for run in range(run_count):
            # Run the scheduler
            result = scheduler_interface.run_scheduler(
                courses=courses,
                students=students,
                config=scheduler_config
            )
            
            if not result:
                continue  # Skip this run if no valid result
                
            # Keep track of the best result
            if best_result is None or result['score'] < best_score:
                best_result = result
                best_score = result['score']
                
            # For a single run, no need to clear student assignments between runs
            if not multiple_runs:
                break
                
            # For multiple runs, clear student assignments for the next attempt
            if run < run_count - 1:  # Don't clear after the last run
                for student in students:
                    student.clear_courses()
        
        # If we didn't get any valid results
        if not best_result:
            return Response(
                {'error': 'Scheduler did not return a valid result after multiple attempts'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Use the name from the result if available, otherwise generate one
        schedule_name = best_result.get('name', f"Schedule_{best_result['score']:.4f}")
        
        # Create a new Schedule entry using the best result
        schedule = Schedule.objects.create(
            name=schedule_name,
            score=best_result['score'],
            is_best=True
        )
        
        # Update all students based on the result and create snapshots
        for student_data in best_result['students']:
            try:
                student = Student.objects.get(id=student_data['student_id'] if 'student_id' in student_data else student_data['id'])
                
                # Get course objects for assignments
                am_course = None
                pm_course = None
                full_day_course = None
                
                if student_data.get('am_course'):
                    am_course = Course.objects.get(name=student_data['am_course'])
                    
                if student_data.get('pm_course'):
                    pm_course = Course.objects.get(name=student_data['pm_course'])
                    
                if student_data.get('full_day_course'):
                    full_day_course = Course.objects.get(name=student_data['full_day_course'])
                
                # Update the actual student record
                student.am_course = am_course
                student.pm_course = pm_course
                student.full_day_course = full_day_course
                student.save()
                
                # Create a snapshot for this student
                ScheduleSnapshot.objects.create(
                    schedule=schedule,
                    student=student,
                    am_course=am_course,
                    pm_course=pm_course,
                    full_day_course=full_day_course,
                    satisfaction_score=student_data.get('satisfaction_score', student_data.get('score', 0.0))
                )
            except Student.DoesNotExist:
                student_id = student_data.get('student_id', student_data.get('id', 'unknown'))
                logger.warning(f"Student with ID {student_id} not found")
            except Course.DoesNotExist:
                student_id = student_data.get('student_id', student_data.get('id', 'unknown'))
                logger.warning(f"Course not found for student {student_id}")
        
        # Mark all other schedules as not the best
        Schedule.objects.exclude(id=schedule.id).update(is_best=False)
        
        return Response({
            'message': 'Scheduler completed successfully',
            'schedule_id': schedule.id,
            'score': schedule.score
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error running scheduler: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Django template views
@login_required
def index(request):
    """Render the main dashboard page"""
    return render(request, 'scheduler/index.html')

@login_required
def courses(request):
    """Render the courses management page"""
    courses = Course.objects.all()
    return render(request, 'scheduler/courses.html', {'courses': courses})

@login_required
def students(request):
    """Render the students management page"""
    students = Student.objects.all()
    courses = Course.objects.all()
    return render(request, 'scheduler/students.html', {
        'students': students,
        'courses': courses
    })

@login_required
def schedules(request):
    """Render the schedules page"""
    schedules = Schedule.objects.all().order_by('-created_at')
    return render(request, 'scheduler/schedules.html', {'schedules': schedules})

@login_required
def schedule_detail(request, pk):
    """Render the schedule detail page"""
    schedule = get_object_or_404(Schedule, pk=pk)
    snapshots = schedule.snapshots.select_related('student', 'am_course', 'pm_course', 'full_day_course')
    
    # Prepare data for the satisfaction chart
    perfect_count = snapshots.filter(satisfaction_score=0).count()
    partial_count = snapshots.filter(satisfaction_score=0.5).count()
    unsatisfied_count = snapshots.filter(satisfaction_score=1.0).count()
    
    # Get sections for this schedule
    sections = Section.objects.all().select_related('course')
    
    # Build context for the template
    context = {
        'schedule': schedule,
        'snapshots': snapshots,
        'perfect_count': perfect_count,
        'partial_count': partial_count,
        'unsatisfied_count': unsatisfied_count,
        'sections': sections
    }
    
    return render(request, 'scheduler/schedule_detail.html', context)

def compare_schedules(request):
    """Render a comparison of two schedules side by side"""
    schedules = Schedule.objects.all().order_by('-created_at')
    schedule1 = None
    schedule2 = None
    student_comparison = {}
    course_comparison = {}
    
    # Get the selected schedules if provided
    schedule1_id = request.GET.get('schedule1')
    schedule2_id = request.GET.get('schedule2')
    
    if schedule1_id and schedule2_id:
        try:
            schedule1 = Schedule.objects.get(id=schedule1_id)
            schedule2 = Schedule.objects.get(id=schedule2_id)
            
            # Get snapshots for both schedules
            snapshots1 = schedule1.snapshots.select_related(
                'student', 'am_course', 'pm_course', 'full_day_course'
            )
            snapshots2 = schedule2.snapshots.select_related(
                'student', 'am_course', 'pm_course', 'full_day_course'
            )
            
            # Build student comparison data
            student_map1 = {s.student.id: s for s in snapshots1}
            student_map2 = {s.student.id: s for s in snapshots2}
            
            all_student_ids = set(student_map1.keys()) | set(student_map2.keys())
            
            for student_id in all_student_ids:
                snapshot1 = student_map1.get(student_id)
                snapshot2 = student_map2.get(student_id)
                
                score1 = snapshot1.satisfaction_score if snapshot1 else 1.0  # 1.0 means worst score if not assigned
                score2 = snapshot2.satisfaction_score if snapshot2 else 1.0
                
                # Only use the name from one of the snapshots if available
                name = ""
                if snapshot1:
                    student = snapshot1.student
                    name = f"{student.first_name} {student.last_name}"
                elif snapshot2:
                    student = snapshot2.student
                    name = f"{student.first_name} {student.last_name}"
                
                # Calculate difference (positive means schedule1 is better, negative means schedule2 is better)
                diff = score2 - score1
                
                student_comparison[student_id] = {
                    'name': name,
                    'score1': score1,
                    'score2': score2,
                    'diff': diff
                }
            
            # Build course fill comparison data
            courses = Course.objects.all()
            
            for course in courses:
                count1 = 0
                count2 = 0
                
                # Count students in this course for schedule 1
                for snapshot in snapshots1:
                    if (snapshot.am_course and snapshot.am_course.id == course.id) or \
                       (snapshot.pm_course and snapshot.pm_course.id == course.id) or \
                       (snapshot.full_day_course and snapshot.full_day_course.id == course.id):
                        count1 += 1
                
                # Count students in this course for schedule 2
                for snapshot in snapshots2:
                    if (snapshot.am_course and snapshot.am_course.id == course.id) or \
                       (snapshot.pm_course and snapshot.pm_course.id == course.id) or \
                       (snapshot.full_day_course and snapshot.full_day_course.id == course.id):
                        count2 += 1
                
                course_comparison[course.name] = {
                    'max': course.max_students,
                    'count1': count1,
                    'count2': count2,
                    'diff': count1 - count2
                }
                
        except Schedule.DoesNotExist:
            pass
    
    return render(request, 'scheduler/compare_schedules.html', {
        'schedules': schedules,
        'schedule1': schedule1,
        'schedule2': schedule2,
        'student_comparison': student_comparison,
        'course_comparison': course_comparison
    })

@login_required
def user_preferences(request):
    """Render the user preferences page"""
    # Get user preferences or create default if none exist
    preferences = None
    preferences, created = UserPreference.objects.get_or_create(user=request.user)
    
    # Set default widget configuration if this is a new user
    if created:
        preferences.widgets = [
            'student_summary', 
            'course_fill', 
            'satisfaction_charts', 
            'recent_schedules'
        ]
        preferences.save()
    
    return render(request, 'scheduler/user_preferences.html', {
        'preferences': preferences
    })

def rate_limited_error(request, exception=None):
    """View that's rendered when a user exceeds the rate limit"""
    context = {
        'title': 'Too Many Requests',
        'message': 'You have made too many requests in a short period of time. '
                  'Please wait a few minutes before trying again.',
        'error_code': 429
    }
    return render(request, 'scheduler/error.html', context, status=429)


@login_required
def advanced_scheduler(request):
    """Render the advanced scheduler configuration page"""
    # Get user preferences or create default if none exist
    preferences = None
    if request.user.is_authenticated:
        preferences, created = UserPreference.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Process the form submission and redirect to the API
        iterations = int(request.POST.get('iterations', 1000))
        min_course_fill = float(request.POST.get('min_course_fill', 0.75))
        early_stop_score = float(request.POST.get('early_stop_score', 0.0))
        time_limit_seconds = int(request.POST.get('time_limit_seconds', 30))
        multiple_runs = 'multiple_runs' in request.POST
        run_count = int(request.POST.get('run_count', 3)) if multiple_runs else 1
        retain_all_runs = request.POST.get('retain_all_runs', 'best_only')
        priority_weight = request.POST.get('priority_weight', 'standard')
        
        # Handle custom thresholds
        custom_thresholds_enabled = 'custom_thresholds_enabled' in request.POST
        satisfaction_thresholds = None
        if custom_thresholds_enabled:
            satisfaction_thresholds = {
                'perfect': float(request.POST.get('perfect_threshold', 0.2)),
                'good': float(request.POST.get('good_threshold', 0.4)),
                'partial': float(request.POST.get('partial_threshold', 0.6)),
                'poor': float(request.POST.get('poor_threshold', 0.8))
            }
            
        # Handle custom priority weights
        custom_weights = None
        if priority_weight == 'custom':
            custom_weights = {
                1: float(request.POST.get('priority1_weight', 3.0)),
                2: float(request.POST.get('priority2_weight', 2.0)),
                3: float(request.POST.get('priority3_weight', 1.0))
            }
        
        # Prepare configuration
        config = {
            'iterations': iterations,
            'min_course_fill': min_course_fill,
            'early_stop_score': early_stop_score,
            'time_limit_seconds': time_limit_seconds,
            'multiple_runs': multiple_runs,
            'run_count': run_count,
            'retain_all_runs': retain_all_runs,
            'priority_weight': priority_weight
        }
        
        if custom_weights:
            config['custom_weights'] = custom_weights
            
        if satisfaction_thresholds:
            config['satisfaction_thresholds'] = satisfaction_thresholds
        
        # Call the API endpoint with the advanced configuration
        request.POST = config  # Replace POST data with our config
        response = run_scheduler(request)
        
        if response.status_code == 200:
            schedule_id = response.data.get('schedule_id')
            return redirect('schedule_detail', pk=schedule_id)
        
        # If there was an error, return to the form with the error message
        return render(request, 'scheduler/advanced_scheduler.html', {
            'preferences': preferences,
            'error': response.data.get('error', 'An error occurred during scheduling')
        })
    
    return render(request, 'scheduler/advanced_scheduler.html', {
        'preferences': preferences
    })

@csrf_exempt
def save_preferences(request):
    """Save user preferences via AJAX"""
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Authentication required'}, status=403)
        
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST method required'}, status=400)
        
    preferences, created = UserPreference.objects.get_or_create(user=request.user)
    
    # Update theme preferences
    if 'theme' in request.POST:
        preferences.theme = request.POST.get('theme')
    
    # Update widget preferences
    if 'widget_order' in request.POST:
        widget_order = request.POST.get('widget_order')
        if widget_order:
            preferences.widget_order = widget_order.split(',')
    
    # Update widget visibility
    widgets = request.POST.getlist('widgets')
    if widgets:
        preferences.widgets = widgets
    
    # Update view preferences
    if 'default_schedule_view' in request.POST:
        preferences.default_schedule_view = request.POST.get('default_schedule_view')
    
    if 'entries_per_page' in request.POST:
        preferences.entries_per_page = int(request.POST.get('entries_per_page'))
    
    # Update scheduler defaults
    if 'default_iterations' in request.POST:
        preferences.default_iterations = int(request.POST.get('default_iterations'))
    
    if 'default_min_course_fill' in request.POST:
        preferences.default_min_course_fill = float(request.POST.get('default_min_course_fill'))
    
    if 'default_priority_weight' in request.POST:
        preferences.default_priority_weight = request.POST.get('default_priority_weight')
    
    # Update notification preferences
    notifications = request.POST.getlist('notifications')
    if notifications:
        preferences.notifications = notifications
    
    if 'notification_duration' in request.POST:
        preferences.notification_duration = int(request.POST.get('notification_duration'))
    
    # Custom satisfaction thresholds
    if 'custom_thresholds' in request.POST:
        try:
            custom_thresholds = json.loads(request.POST.get('custom_thresholds'))
            preferences.custom_satisfaction_thresholds = custom_thresholds
        except json.JSONDecodeError:
            pass
    
    preferences.save()
    
    return JsonResponse({'status': 'success', 'message': 'Preferences saved successfully'})

@login_required
def run_scheduler_ui(request):
    """Render the scheduler configuration page with user preferences"""
    # Get user preferences or create default if none exist
    preferences = None
    if request.user.is_authenticated:
        preferences, created = UserPreference.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Process the form submission and redirect to the API
        iterations = int(request.POST.get('iterations', 1000))
        min_course_fill = float(request.POST.get('min_course_fill', 0.75))
        early_stop_score = float(request.POST.get('early_stop_score', 0.0))
        multiple_runs = 'multiple_runs' in request.POST
        run_count = int(request.POST.get('run_count', 3)) if multiple_runs else 1
        priority_weight = request.POST.get('priority_weight', 'standard')
        
        config = {
            'iterations': iterations,
            'min_course_fill': min_course_fill,
            'early_stop_score': early_stop_score,
            'multiple_runs': multiple_runs,
            'run_count': run_count,
            'priority_weight': priority_weight
        }
        
        # Save preferences if user is authenticated
        if request.user.is_authenticated and preferences:
            preferences.default_iterations = iterations
            preferences.default_min_course_fill = min_course_fill
            preferences.default_priority_weight = priority_weight
            preferences.save()
        
        # Call the API endpoint
        response = run_scheduler(request._request)
        
        if response.status_code == 200:
            schedule_id = response.data.get('schedule_id')
            return redirect('schedule_detail', pk=schedule_id)
        else:
            error = response.data.get('error', 'Unknown error')
            return render(request, 'scheduler/run_scheduler.html', {
                'error': error,
                'config': config
            })
    
    # Show the form for GET requests
    configs = SchedulerConfig.objects.all().order_by('-created_at')[:5]  # Get last 5 configs
    return render(request, 'scheduler/run_scheduler.html', {'configs': configs})

# Ninja API endpoints
@api.get("/courses", response=List[dict])
def list_courses(request):
    """List all courses"""
    courses = Course.objects.all()
    return CourseSerializer(courses, many=True).data

@api.get("/students", response=List[dict])
def list_students(request):
    """List all students"""
    students = Student.objects.all()
    return StudentSerializer(students, many=True).data

@api.get("/schedules", response=List[dict])
def list_schedules(request):
    """List all schedules"""
    schedules = Schedule.objects.all().order_by('-created_at')
    return ScheduleSerializer(schedules, many=True).data

@api.get("/schedules/{schedule_id}", response=dict)
def get_schedule(request, schedule_id: int):
    """Get a specific schedule"""
    schedule = get_object_or_404(Schedule, id=schedule_id)
    return ScheduleSerializer(schedule).data

@api.post("/schedules/run", response=dict)
def run_scheduler_api(request, config: dict):
    """Run the scheduler with the given configuration"""
    iterations = config.get('iterations', 1000)
    min_course_fill = config.get('min_course_fill', 0.75)
    early_stop_score = config.get('early_stop_score', 0.0)
    
    # Create a request object for the DRF API view
    request._request.data = {'config': config}
    response = run_scheduler(request._request)
    
    if response.status_code == 200:
        return response.data
    else:
        return {'error': response.data.get('error', 'Unknown error')}
