"""
Tests for the scheduler app views.
"""
import pytest
from django.urls import reverse
from django.test import Client
from rest_framework import status
from scheduler.models import Student, Course, Schedule, Section
from django.contrib.auth.models import User


@pytest.fixture
def authenticated_client():
    """Create an authenticated client."""
    client = Client()
    user = User.objects.create_user(username='testuser', password='12345')
    client.login(username='testuser', password='12345')
    return client


@pytest.mark.django_db
class TestStudentViews:
    """Tests for the student views."""
    
    def test_student_list_view(self, authenticated_client):
        """Test the student list view."""
        # Create test students
        Student.objects.create(name="Test Student 1", email="test1@example.com", grade=9)
        Student.objects.create(name="Test Student 2", email="test2@example.com", grade=10)
        
        # Test the view
        response = authenticated_client.get(reverse('students'))
        assert response.status_code == 200
        assert 'Test Student 1' in str(response.content)
        assert 'Test Student 2' in str(response.content)
    
    def test_add_student_api(self, authenticated_client):
        """Test the add student API endpoint."""
        url = reverse('add_student')
        data = {
            'name': 'New Student',
            'email': 'new@example.com',
            'grade': 11
        }
        
        response = authenticated_client.post(url, data, content_type='application/json')
        assert response.status_code == 201
        assert Student.objects.filter(name='New Student').exists()
    
    def test_clear_all_students_api(self, authenticated_client):
        """Test the clear all students API endpoint."""
        # Create test students
        Student.objects.create(name="Test Student", email="test@example.com", grade=9)
        assert Student.objects.count() == 1
        
        # Test the view
        url = reverse('clear_all_students')
        response = authenticated_client.delete(url)
        assert response.status_code == 200
        assert Student.objects.count() == 0


@pytest.mark.django_db
class TestCourseViews:
    """Tests for the course views."""
    
    def test_course_list_view(self, authenticated_client):
        """Test the course list view."""
        # Create test courses
        Course.objects.create(name="Algebra", subject="Mathematics", grade_level=9)
        Course.objects.create(name="Biology", subject="Science", grade_level=9)
        
        # Test the view
        response = authenticated_client.get(reverse('courses'))
        assert response.status_code == 200
        assert 'Algebra' in str(response.content)
        assert 'Biology' in str(response.content)
    
    def test_add_course_api(self, authenticated_client):
        """Test the add course API endpoint."""
        url = reverse('add_course')
        data = {
            'name': 'Chemistry',
            'subject': 'Science',
            'grade_level': 10,
            'max_students': 25
        }
        
        response = authenticated_client.post(url, data, content_type='application/json')
        assert response.status_code == 201
        assert Course.objects.filter(name='Chemistry').exists()
    
    def test_clear_all_courses_api(self, authenticated_client):
        """Test the clear all courses API endpoint."""
        # Create test course
        Course.objects.create(name="Test Course", subject="Test", grade_level=9)
        assert Course.objects.count() == 1
        
        # Test the view
        url = reverse('clear_all_courses')
        response = authenticated_client.delete(url)
        assert response.status_code == 200
        assert Course.objects.count() == 0


@pytest.mark.django_db
class TestScheduleViews:
    """Tests for the schedule views."""
    
    def test_schedule_list_view(self, authenticated_client):
        """Test the schedule list view."""
        # Create test schedule
        Schedule.objects.create(name="Fall 2025", is_best=True)
        
        # Test the view
        response = authenticated_client.get(reverse('schedules'))
        assert response.status_code == 200
        assert 'Fall 2025' in str(response.content)
    
    def test_schedule_detail_view(self, authenticated_client):
        """Test the schedule detail view."""
        # Create test data
        schedule = Schedule.objects.create(name="Test Schedule", is_best=True)
        course = Course.objects.create(name="Test Course", subject="Test", grade_level=9)
        Section.objects.create(course=course, schedule=schedule, period=1, teacher="Test Teacher")
        
        # Test the view
        url = reverse('schedule_detail', args=[schedule.id])
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert 'Test Schedule' in str(response.content)
        assert 'Test Course' in str(response.content)
        assert 'Test Teacher' in str(response.content)


@pytest.mark.django_db
class TestORToolsScheduler:
    """Tests for the OR-Tools scheduler."""
    
    def test_ortools_scheduler_api(self, authenticated_client):
        """Test the OR-Tools scheduler API endpoint."""
        # Create test data
        for i in range(10):
            Student.objects.create(name=f"Student {i}", email=f"student{i}@example.com", grade=9)
        
        for i in range(5):
            Course.objects.create(name=f"Course {i}", subject=f"Subject {i}", grade_level=9, max_students=25)
        
        # Test the API
        url = reverse('run_scheduler')
        data = {
            'algorithm': 'ortools',
            'max_iterations': 100,
            'timeout_seconds': 10
        }
        
        response = authenticated_client.post(url, data, content_type='application/json')
        assert response.status_code == 200
        assert 'schedule_id' in response.json()
        assert Schedule.objects.filter(id=response.json()['schedule_id']).exists()
