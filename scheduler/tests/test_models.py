"""
Tests for the scheduler app models.
"""
import pytest
from django.test import TestCase
from scheduler.models import Student, Course, Schedule, Section

@pytest.mark.django_db
class TestStudentModel:
    """Tests for the Student model."""
    
    def test_student_creation(self):
        """Test creating a student."""
        student = Student.objects.create(
            name="John Doe",
            email="john@example.com",
            grade=10
        )
        assert student.name == "John Doe"
        assert student.email == "john@example.com"
        assert student.grade == 10
    
    def test_student_str(self):
        """Test the string representation of a student."""
        student = Student.objects.create(
            name="Jane Smith",
            email="jane@example.com",
            grade=11
        )
        assert str(student) == "Jane Smith"
        
@pytest.mark.django_db
class TestCourseModel:
    """Tests for the Course model."""
    
    def test_course_creation(self):
        """Test creating a course."""
        course = Course.objects.create(
            name="Algebra",
            subject="Mathematics",
            grade_level=10,
            max_students=25,
            prerequsites="Basic Math"
        )
        assert course.name == "Algebra"
        assert course.subject == "Mathematics"
        assert course.grade_level == 10
        assert course.max_students == 25
        assert course.prerequsites == "Basic Math"
    
    def test_course_str(self):
        """Test the string representation of a course."""
        course = Course.objects.create(
            name="Biology",
            subject="Science",
            grade_level=9
        )
        assert str(course) == "Biology"

@pytest.mark.django_db
class TestScheduleModel:
    """Tests for the Schedule model."""
    
    def test_schedule_creation(self):
        """Test creating a schedule."""
        schedule = Schedule.objects.create(
            name="Fall 2025",
            is_best=True
        )
        assert schedule.name == "Fall 2025"
        assert schedule.is_best is True
    
    def test_schedule_str(self):
        """Test the string representation of a schedule."""
        schedule = Schedule.objects.create(
            name="Spring 2026",
            is_best=False
        )
        assert str(schedule) == "Spring 2026"

@pytest.mark.django_db
class TestSectionModel:
    """Tests for the Section model."""
    
    def test_section_creation(self):
        """Test creating a section."""
        course = Course.objects.create(
            name="Chemistry",
            subject="Science",
            grade_level=11
        )
        schedule = Schedule.objects.create(name="Test Schedule")
        
        section = Section.objects.create(
            course=course,
            schedule=schedule,
            period=3,
            room="Lab 101",
            teacher="Dr. Smith"
        )
        
        assert section.course.name == "Chemistry"
        assert section.schedule.name == "Test Schedule"
        assert section.period == 3
        assert section.room == "Lab 101"
        assert section.teacher == "Dr. Smith"
    
    def test_section_str(self):
        """Test the string representation of a section."""
        course = Course.objects.create(name="Physics", subject="Science", grade_level=12)
        schedule = Schedule.objects.create(name="Test Schedule")
        
        section = Section.objects.create(
            course=course,
            schedule=schedule,
            period=4,
            teacher="Dr. Johnson"
        )
        
        assert str(section) == "Physics - Period 4 (Dr. Johnson)"
