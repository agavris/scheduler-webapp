"""
Main views for the scheduler application.
Original contents from views.py.
"""
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

from ..models import Course, Student, Section, Schedule, ScheduleSnapshot, SchedulerConfig, UserPreference
from ..serializers import (
    CourseSerializer, StudentSerializer, SectionSerializer,
    ScheduleSerializer, ScheduleSnapshotSerializer, SchedulerConfigSerializer,
    RequestSerializer
)

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
        students = Student.objects.all()
        serializer = StudentSerializer(students, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def with_sections(self, request, pk=None):
        """Return a student with their assigned sections"""
        student = self.get_object()
        serializer = StudentSerializer(student)
        return Response(serializer.data)


class SectionViewSet(viewsets.ModelViewSet):
    queryset = Section.objects.all()
    serializer_class = SectionSerializer


class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    
    @action(detail=False, methods=['post'])
    def clear_old_schedules(self, request):
        """Delete all schedules that aren't marked as 'best'"""
        old_schedules = Schedule.objects.filter(is_best=False)
        count = old_schedules.count()
        old_schedules.delete()
        return Response({'message': f'Deleted {count} old schedules.'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def export_csv(self, request, pk=None):
        """Export a schedule to CSV format"""
        schedule = self.get_object()
        
        # Create a CSV file in memory
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        
        # Write header
        writer.writerow(['Student', 'Course', 'Section', 'Time', 'Room', 'Instructor'])
        
        # Write data
        for student in Student.objects.all():
            for section in student.sections.filter(schedule=schedule):
                writer.writerow([
                    student.name,
                    section.course.name,
                    section.name,
                    section.time,
                    section.room,
                    section.instructor
                ])
        
        # Create the HTTP response
        response = HttpResponse(csv_buffer.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="schedule_{schedule.id}_{schedule.name}.csv"'
        
        return response


class SchedulerConfigViewSet(viewsets.ModelViewSet):
    queryset = SchedulerConfig.objects.all()
    serializer_class = SchedulerConfigSerializer


# Data management views
@login_required
@user_passes_test(lambda u: u.is_staff)
def clear_all_students(request):
    """Clear all students from the database"""
    if request.method == 'POST':
        try:
            Student.objects.all().delete()
            return JsonResponse({'status': 'success', 'message': 'All students have been deleted.'})
        except Exception as e:
            logging.error(f"Error clearing students: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Only POST method is allowed.'}, status=405)


@login_required
@user_passes_test(lambda u: u.is_staff)
def clear_all_courses(request):
    """Clear all courses from the database"""
    if request.method == 'POST':
        try:
            Course.objects.all().delete()
            return JsonResponse({'status': 'success', 'message': 'All courses have been deleted.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Only POST method is allowed.'}, status=405)


# Data import and export views
@login_required
@csrf_exempt
def import_courses(request):
    """Import courses from a CSV file"""
    if request.method == 'POST':
        try:
            csv_file = request.FILES.get('file')
            if not csv_file:
                return JsonResponse({'status': 'error', 'message': 'No file uploaded.'}, status=400)
            
            # Check file extension
            if not csv_file.name.endswith('.csv'):
                return JsonResponse({'status': 'error', 'message': 'File must be a CSV.'}, status=400)
            
            # Process CSV
            data = csv_file.read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(data))
            
            courses_added = 0
            sections_added = 0
            
            for row in reader:
                course, created = Course.objects.get_or_create(
                    code=row['Course Code'],
                    defaults={'name': row['Course Name']}
                )
                
                if created:
                    courses_added += 1
                
                # Create section
                section = Section.objects.create(
                    course=course,
                    name=row['Section'],
                    time=row['Time'],
                    room=row['Room'],
                    capacity=int(row['Capacity']),
                    instructor=row['Instructor']
                )
                sections_added += 1
            
            return JsonResponse({
                'status': 'success',
                'message': f'Imported {courses_added} courses and {sections_added} sections.'
            })
        
        except Exception as e:
            logging.error(f"Error importing courses: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Only POST method is allowed.'}, status=405)


@login_required
@csrf_exempt
def import_students(request):
    """Import students and their course preferences from a CSV file"""
    if request.method == 'POST':
        try:
            csv_file = request.FILES.get('file')
            if not csv_file:
                return JsonResponse({'status': 'error', 'message': 'No file uploaded.'}, status=400)
            
            # Check file extension
            if not csv_file.name.endswith('.csv'):
                return JsonResponse({'status': 'error', 'message': 'File must be a CSV.'}, status=400)
            
            # Process CSV
            data = csv_file.read().decode('utf-8')
            df = pd.read_csv(io.StringIO(data))
            
            # Get all course codes from the header except the first column
            course_codes = df.columns[1:].tolist()
            
            # Check if all courses exist
            missing_courses = []
            for code in course_codes:
                if not Course.objects.filter(code=code).exists():
                    missing_courses.append(code)
            
            if missing_courses:
                return JsonResponse({
                    'status': 'error',
                    'message': f'The following courses do not exist: {", ".join(missing_courses)}'
                }, status=400)
            
            students_added = 0
            preferences_added = 0
            
            # Process each student
            for _, row in df.iterrows():
                student_id = str(row[0])
                
                # Create or update student
                student, created = Student.objects.get_or_create(
                    student_id=student_id,
                    defaults={'name': student_id}  # Use ID as name if not provided
                )
                
                if created:
                    students_added += 1
                
                # Add preferences
                for course_code in course_codes:
                    preference = row[course_code]
                    if not pd.isna(preference) and preference:
                        course = Course.objects.get(code=course_code)
                        student.course_preferences.add(course)
                        preferences_added += 1
            
            return JsonResponse({
                'status': 'success',
                'message': f'Imported {students_added} students with {preferences_added} course preferences.'
            })
        
        except Exception as e:
            logging.error(f"Error importing students: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Only POST method is allowed.'}, status=405)


# Scheduler API endpoints
@login_required
@api_view(['POST'])
def run_scheduler(request):
    """Run the scheduler algorithm with the given configuration"""
    try:
        # Get configuration parameters
        data = request.data
        max_iterations = int(data.get('max_iterations', 1000))
        time_limit = int(data.get('time_limit', 30))
        balance_sections = data.get('balance_sections', True)
        honor_preferences = data.get('honor_preferences', True)
        
        # Save configuration
        config = SchedulerConfig.objects.create(
            max_iterations=max_iterations,
            time_limit=time_limit,
            balance_sections=balance_sections,
            honor_preferences=honor_preferences
        )
        
        # Create a new schedule
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        schedule = Schedule.objects.create(
            name=f'Schedule_{timestamp}',
            config=config,
            is_best=False
        )
        
        # Step 1: Get all students and courses
        students = Student.objects.all()
        courses = Course.objects.all()
        
        if not students:
            return Response({
                'status': 'error',
                'message': 'No students found. Please import students first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not courses:
            return Response({
                'status': 'error',
                'message': 'No courses found. Please import courses first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Step 2: Initialize assignments
        for student in students:
            # Get student preferences
            preferred_courses = student.course_preferences.all()
            
            # If honor_preferences is True, only assign preferred courses
            # Otherwise, assign all courses
            target_courses = preferred_courses if honor_preferences else courses
            
            for course in target_courses:
                # Find sections for this course
                sections = Section.objects.filter(course=course)
                
                if not sections:
                    continue
                
                # Find section with the most available capacity
                best_section = max(sections, key=lambda s: s.capacity - s.student_set.count())
                
                # If the section is full, skip
                if best_section.student_set.count() >= best_section.capacity:
                    continue
                
                # Assign student to section
                student.sections.add(best_section)
                
                # Update section's schedule
                best_section.schedule = schedule
                best_section.save()
        
        # Step 3: Run optimization algorithm
        # (Simplified for this example)
        
        # Mark as the best schedule if it's the first one
        if Schedule.objects.count() == 1:
            schedule.is_best = True
            schedule.save()
        
        # Return success response
        return Response({
            'status': 'success',
            'message': 'Scheduler run completed successfully.',
            'schedule_id': schedule.id,
            'schedule_name': schedule.name
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logging.error(f"Error running scheduler: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    schedules = Schedule.objects.all()
    return render(request, 'scheduler/schedules.html', {'schedules': schedules})


@login_required
def schedule_detail(request, pk):
    """Render the schedule detail page"""
    schedule = get_object_or_404(Schedule, pk=pk)
    
    # Group sections by student
    student_sections = {}
    for student in Student.objects.all():
        sections = student.sections.filter(schedule=schedule)
        if sections:
            student_sections[student] = sections
    
    # Calculate statistics
    total_students = len(student_sections)
    total_sections = sum(len(sections) for sections in student_sections.values())
    avg_sections_per_student = total_sections / total_students if total_students > 0 else 0
    
    return render(request, 'scheduler/schedule_detail.html', {
        'schedule': schedule,
        'student_sections': student_sections,
        'stats': {
            'total_students': total_students,
            'total_sections': total_sections,
            'avg_sections_per_student': avg_sections_per_student
        }
    })


@login_required
def compare_schedules(request):
    """Render a comparison of two schedules side by side"""
    schedules = Schedule.objects.all()
    
    # Get selected schedules from request
    schedule1_id = request.GET.get('schedule1')
    schedule2_id = request.GET.get('schedule2')
    
    schedule1 = None
    schedule2 = None
    comparison = None
    
    if schedule1_id and schedule2_id:
        schedule1 = get_object_or_404(Schedule, pk=schedule1_id)
        schedule2 = get_object_or_404(Schedule, pk=schedule2_id)
        
        # Calculate comparison metrics
        comparison = {
            'total_students': Student.objects.count(),
            'schedule1': {
                'name': schedule1.name,
                'student_count': 0,
                'section_count': 0,
                'avg_sections_per_student': 0
            },
            'schedule2': {
                'name': schedule2.name,
                'student_count': 0,
                'section_count': 0,
                'avg_sections_per_student': 0
            },
            'diff': {
                'student_count': 0,
                'section_count': 0,
                'avg_sections_per_student': 0
            }
        }
        
        # Calculate statistics for schedule 1
        student_sections1 = {}
        for student in Student.objects.all():
            sections = student.sections.filter(schedule=schedule1)
            if sections:
                student_sections1[student] = sections
        
        schedule1_student_count = len(student_sections1)
        schedule1_section_count = sum(len(sections) for sections in student_sections1.values())
        schedule1_avg = (
            schedule1_section_count / schedule1_student_count 
            if schedule1_student_count > 0 else 0
        )
        
        comparison['schedule1']['student_count'] = schedule1_student_count
        comparison['schedule1']['section_count'] = schedule1_section_count
        comparison['schedule1']['avg_sections_per_student'] = schedule1_avg
        
        # Calculate statistics for schedule 2
        student_sections2 = {}
        for student in Student.objects.all():
            sections = student.sections.filter(schedule=schedule2)
            if sections:
                student_sections2[student] = sections
        
        schedule2_student_count = len(student_sections2)
        schedule2_section_count = sum(len(sections) for sections in student_sections2.values())
        schedule2_avg = (
            schedule2_section_count / schedule2_student_count 
            if schedule2_student_count > 0 else 0
        )
        
        comparison['schedule2']['student_count'] = schedule2_student_count
        comparison['schedule2']['section_count'] = schedule2_section_count
        comparison['schedule2']['avg_sections_per_student'] = schedule2_avg
        
        # Calculate differences
        comparison['diff']['student_count'] = schedule2_student_count - schedule1_student_count
        comparison['diff']['section_count'] = schedule2_section_count - schedule1_section_count
        comparison['diff']['avg_sections_per_student'] = schedule2_avg - schedule1_avg
    
    return render(request, 'scheduler/compare.html', {
        'schedules': schedules,
        'schedule1': schedule1,
        'schedule2': schedule2,
        'comparison': comparison
    })


@login_required
def user_preferences(request):
    """Render the user preferences page"""
    # Get or create user preferences
    preference, created = UserPreference.objects.get_or_create(
        user=request.user,
        defaults={
            'theme': 'light',
            'items_per_page': 10,
            'notifications_enabled': True
        }
    )
    
    return render(request, 'scheduler/preferences.html', {
        'preference': preference
    })


def rate_limited_error(request, exception=None):
    """View that's rendered when a user exceeds the rate limit"""
    return render(request, 'scheduler/rate_limited.html', {
        'retry_after': getattr(exception, 'retry_after', None)
    }, status=429)


@login_required
def advanced_scheduler(request):
    """Render the advanced scheduler configuration page"""
    # Get all available data
    students = Student.objects.all()
    courses = Course.objects.all()
    
    # Get previous configurations
    configs = SchedulerConfig.objects.all().order_by('-created_at')[:5]
    
    # Get system stats
    stats = {
        'total_students': students.count(),
        'total_courses': courses.count(),
        'total_sections': Section.objects.count(),
        'total_schedules': Schedule.objects.count()
    }
    
    # If form is submitted
    if request.method == 'POST':
        try:
            # Parse configuration parameters
            config_data = {
                'max_iterations': int(request.POST.get('max_iterations', 1000)),
                'time_limit': int(request.POST.get('time_limit', 30)),
                'balance_sections': request.POST.get('balance_sections') == 'on',
                'honor_preferences': request.POST.get('honor_preferences') == 'on',
                'optimization_strategy': request.POST.get('optimization_strategy', 'balanced')
            }
            
            # Additional parameters based on strategy
            if config_data['optimization_strategy'] == 'preferences':
                config_data['preference_weight'] = float(request.POST.get('preference_weight', 0.8))
            elif config_data['optimization_strategy'] == 'balance':
                config_data['balance_weight'] = float(request.POST.get('balance_weight', 0.8))
            
            # Save configuration
            config = SchedulerConfig.objects.create(**config_data)
            
            # Create a new schedule
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            schedule = Schedule.objects.create(
                name=request.POST.get('schedule_name', f'Schedule_{timestamp}'),
                config=config,
                is_best=False
            )
            
            # Run the scheduler (simplified, would call the scheduler algorithm here)
            messages.success(request, 'Scheduler started successfully. This may take a few moments.')
            return redirect('schedule_detail', pk=schedule.id)
        
        except Exception as e:
            messages.error(request, f'Error starting scheduler: {str(e)}')
    
    return render(request, 'scheduler/advanced_scheduler.html', {
        'students': students,
        'courses': courses,
        'configs': configs,
        'stats': stats
    })


@login_required
@csrf_exempt
def save_preferences(request):
    """Save user preferences via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Get or create user preferences
            preference, created = UserPreference.objects.get_or_create(
                user=request.user
            )
            
            # Update preferences
            if 'theme' in data:
                preference.theme = data['theme']
            
            if 'items_per_page' in data:
                preference.items_per_page = int(data['items_per_page'])
            
            if 'notifications_enabled' in data:
                preference.notifications_enabled = data['notifications_enabled']
            
            # Additional preferences can be added here
            
            preference.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Preferences saved successfully.'
            })
        
        except Exception as e:
            logging.error(f"Error saving preferences: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f'An error occurred: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Only POST method is allowed.'
    }, status=405)


@login_required
def run_scheduler_ui(request):
    """Render the scheduler configuration page with user preferences"""
    # Get all available data
    students = Student.objects.all()
    courses = Course.objects.all()
    
    # Get user preferences
    preference, created = UserPreference.objects.get_or_create(
        user=request.user
    )
    
    # Default configuration
    default_config = {
        'max_iterations': 1000,
        'time_limit': 30,
        'balance_sections': True,
        'honor_preferences': True,
        'optimization_strategy': 'balanced'
    }
    
    # Apply user preferences to configuration
    if preference.scheduler_preferences:
        try:
            user_config = json.loads(preference.scheduler_preferences)
            default_config.update(user_config)
        except:
            # If there's an error parsing preferences, use defaults
            pass
    
    # Check if we have data
    has_data = students.exists() and courses.exists()
    
    return render(request, 'scheduler/run_scheduler.html', {
        'students': students,
        'courses': courses,
        'config': default_config,
        'has_data': has_data
    })


# Ninja API endpoints
api = NinjaAPI()

@api.get("/courses")
def list_courses(request):
    """List all courses"""
    courses = Course.objects.all()
    return [{"id": c.id, "name": c.name, "code": c.code} for c in courses]


@api.get("/students")
def list_students(request):
    """List all students"""
    students = Student.objects.all()
    return [{"id": s.id, "name": s.name, "student_id": s.student_id} for s in students]


@api.get("/schedules")
def list_schedules(request):
    """List all schedules"""
    schedules = Schedule.objects.all()
    return [{"id": s.id, "name": s.name, "is_best": s.is_best} for s in schedules]


@api.get("/schedules/{schedule_id}")
def get_schedule(request, schedule_id: int):
    """Get a specific schedule"""
    schedule = get_object_or_404(Schedule, id=schedule_id)
    return {"id": schedule.id, "name": schedule.name, "is_best": schedule.is_best}


@api.post("/run-scheduler")
def run_scheduler_api(request, config: dict):
    """Run the scheduler with the given configuration"""
    # Here we would call the same scheduler logic as in the view
    # But returning the results in a format suitable for API consumption
    
    return {
        "status": "success",
        "message": "Scheduler started",
        "config": config
    }
