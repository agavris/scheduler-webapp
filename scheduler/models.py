from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import json
from django.conf import settings


class UserPreference(models.Model):
    """
    Stores customization preferences for users including UI, scheduling, and display options
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='preferences')
    theme = models.CharField(max_length=50, default='default')
    widgets = models.JSONField(default=list)
    widget_order = models.JSONField(default=list)
    default_schedule_view = models.CharField(max_length=20, default='list')
    entries_per_page = models.IntegerField(default=25)
    default_iterations = models.IntegerField(default=1000)
    default_min_course_fill = models.FloatField(default=0.75)
    default_priority_weight = models.CharField(max_length=20, default='standard')
    notifications = models.JSONField(default=list)
    notification_duration = models.IntegerField(default=5)
    advanced_options = models.JSONField(default=dict)
    
    # Additional scheduler customizations
    customize_priority_weights = models.JSONField(default=dict, help_text="Custom weight per priority level")
    custom_satisfaction_thresholds = models.JSONField(default=dict, help_text="Custom thresholds for satisfaction levels")
    
    # Report and export settings
    export_formats = models.JSONField(default=list, help_text="Available formats for exporting data")
    email_reports = models.BooleanField(default=False)
    
    # Dashboard settings
    show_analytics = models.BooleanField(default=True)
    charts_theme = models.CharField(max_length=50, default='default')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Preferences for {self.user.username}"
    
    def get_default_widgets(self):
        """Return default widgets if none are set"""
        if not self.widgets:
            return [
                'student_summary', 
                'course_fill', 
                'satisfaction_charts', 
                'recent_schedules'
            ]
        return self.widgets
    
    def get_satisfaction_thresholds(self):
        """Get satisfaction thresholds with defaults if not set"""
        defaults = {
            'perfect': 0.2,
            'good': 0.4,
            'partial': 0.6,
            'poor': 0.8
        }
        
        if not self.custom_satisfaction_thresholds:
            return defaults
            
        # Merge defaults with custom thresholds
        return {**defaults, **self.custom_satisfaction_thresholds}
    
    def get_priority_weights(self):
        """Get priority weights with defaults if not set"""
        # Standard priority weights
        if self.default_priority_weight == 'standard':
            return {1: 1.0, 2: 0.8, 3: 0.6}
        # Strong priority weights
        elif self.default_priority_weight == 'strong':
            return {1: 1.0, 2: 0.6, 3: 0.3}
        # Balanced priority weights
        elif self.default_priority_weight == 'balanced':
            return {1: 1.0, 2: 0.9, 3: 0.8}
        # Custom weights
        elif self.customize_priority_weights:
            return self.customize_priority_weights
        # Default to standard if nothing else
        else:
            return {1: 1.0, 2: 0.8, 3: 0.6}


class Course(models.Model):
    """
    Represents a course offering with a name and timeslot
    """
    name = models.CharField(max_length=255, unique=True)
    time_slot = models.CharField(max_length=10, choices=[
        ('AM', 'Morning'),
        ('PM', 'Afternoon'),
        ('FullDay', 'Full Day'),
    ])
    max_students = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.name} ({self.time_slot})"

class Student(models.Model):
    """
    Represents a student with their details and course preferences
    """
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    grade = models.IntegerField(default=9)
    priority = models.IntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Priority level (1-5, with 1 being highest)"
    )
    
    # Preferences as JSON arrays
    am_preferences = models.JSONField(default=list)
    pm_preferences = models.JSONField(default=list)
    
    # Currently enrolled courses
    am_course = models.ForeignKey('Course', null=True, blank=True, on_delete=models.SET_NULL, related_name='am_students')
    pm_course = models.ForeignKey('Course', null=True, blank=True, on_delete=models.SET_NULL, related_name='pm_students')
    full_day_course = models.ForeignKey('Course', null=True, blank=True, on_delete=models.SET_NULL, related_name='full_day_students')
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    def clear_courses(self):
        """Remove student from all courses."""
        self.am_course = None
        self.pm_course = None
        self.full_day_course = None
        self.save()
        
    def clear_enrollments(self):
        """Alias for clear_courses to maintain compatibility."""
        self.clear_courses()
        
    def get_am_preferences(self):
        """Get AM preferences for the student"""
        return self.am_preferences
        
    def get_pm_preferences(self):
        """Get PM preferences for the student"""
        return self.pm_preferences
    
    def satisfaction_score(self):
        """Calculate student satisfaction based on course assignments"""
        score = 0.0
        max_score = 0
        
        # Calculate AM satisfaction
        if self.am_course and self.am_preferences:
            if self.am_course.name in self.am_preferences:
                position = self.am_preferences.index(self.am_course.name)
                score += position  # Lower index = higher preference = lower score
            else:
                score += len(self.am_preferences)  # Worst possible score is length of preference list
            max_score += len(self.am_preferences) - 1
        
        # Calculate PM satisfaction
        if self.pm_course and self.pm_preferences:
            if self.pm_course.name in self.pm_preferences:
                position = self.pm_preferences.index(self.pm_course.name)
                score += position  # Lower index = higher preference = lower score
            else:
                score += len(self.pm_preferences)  # Worst possible score is length of preference list
            max_score += len(self.pm_preferences) - 1
        
        # Calculate full-day course satisfaction
        if self.full_day_course:
            total_positions = 0
            total_max = 0
            
            # Check if full-day course is in AM preferences
            if self.am_preferences and self.full_day_course.name in self.am_preferences:
                position = self.am_preferences.index(self.full_day_course.name)
                total_positions += position
                total_max += len(self.am_preferences) - 1
            else:
                if self.am_preferences:
                    total_positions += len(self.am_preferences)
                    total_max += len(self.am_preferences) - 1
            
            # Check if full-day course is in PM preferences
            if self.pm_preferences and self.full_day_course.name in self.pm_preferences:
                position = self.pm_preferences.index(self.full_day_course.name)
                total_positions += position
                total_max += len(self.pm_preferences) - 1
            else:
                if self.pm_preferences:
                    total_positions += len(self.pm_preferences)
                    total_max += len(self.pm_preferences) - 1
            
            # Average the positions if we have any
            if total_max > 0:
                score = total_positions
                max_score = total_max
        
        # Normalize score to be between 0 and 1
        if max_score > 0:
            return score / max_score
        return 0.0  # No preferences or no courses assigned

class Section(models.Model):
    """
    Represents a section of a course with enrolled students
    Equivalent to the Section struct in Go code
    """
    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name='section')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Section: {self.course.name}"
    
    @property
    def max_students(self):
        return self.course.max_students
    
    @property
    def enrolled_students_count(self):
        return self.get_students().count()
    
    def get_students(self):
        """Get all students enrolled in this section"""
        if self.course.time_slot == 'AM':
            return Student.objects.filter(am_course=self.course)
        elif self.course.time_slot == 'PM':
            return Student.objects.filter(pm_course=self.course)
        else:  # FullDay
            return Student.objects.filter(full_day_course=self.course)
    
    def add_student(self, student):
        """Add a student to this section"""
        if self.enrolled_students_count < self.max_students:
            if self.course.time_slot == 'AM':
                student.am_course = self.course
            elif self.course.time_slot == 'PM':
                student.pm_course = self.course
            else:  # FullDay
                student.full_day_course = self.course
            student.save()
            return True
        return False
    
    def remove_student(self, student):
        """Remove a student from this section"""
        if self.course.time_slot == 'AM' and student.am_course == self.course:
            student.am_course = None
            student.save()
            return True
        elif self.course.time_slot == 'PM' and student.pm_course == self.course:
            student.pm_course = None
            student.save()
            return True
        elif student.full_day_course == self.course:
            student.full_day_course = None
            student.save()
            return True
        return False
    
    def clear_students(self):
        """Remove all students from this section"""
        if self.course.time_slot == 'AM':
            Student.objects.filter(am_course=self.course).update(am_course=None)
        elif self.course.time_slot == 'PM':
            Student.objects.filter(pm_course=self.course).update(pm_course=None)
        else:  # FullDay
            Student.objects.filter(full_day_course=self.course).update(full_day_course=None)

class Schedule(models.Model):
    """
    Represents a complete schedule with student assignments and score
    """
    name = models.CharField(max_length=255)
    score = models.FloatField(default=0.0)
    is_best = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} (Score: {self.score:.2f})"
    
    def save_snapshot(self):
        """Save the current state of all student enrollments"""
        students = Student.objects.all()
        
        for student in students:
            # Save student's current course assignments
            snapshot = ScheduleSnapshot(
                schedule=self,
                student=student,
                am_course=student.am_course,
                pm_course=student.pm_course,
                full_day_course=student.full_day_course,
                satisfaction_score=student.satisfaction_score()
            )
            snapshot.save()
    
    def calculate_metrics(self):
        """Calculate performance metrics for this schedule"""
        perfect_count = 0
        partial_count = 0
        unsatisfied_count = 0
        total_score = 0.0
        
        snapshots = self.snapshots.all()
        for snapshot in snapshots:
            score = snapshot.satisfaction_score
            total_score += score
            
            if score >= 0.9:  # 90% or better is perfect
                perfect_count += 1
            elif score > 0:  # Any score above 0 is partial
                partial_count += 1
            else:  # Score of 0 means unsatisfied
                unsatisfied_count += 1
        
        self.score = total_score / snapshots.count() if snapshots.exists() else 0
        self.perfect_count = perfect_count
        self.partial_count = partial_count
        self.unsatisfied_count = unsatisfied_count
        self.save()

class ScheduleSnapshot(models.Model):
    """
    Represents a snapshot of a student's course assignments in a schedule
    """
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='snapshots')
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    
    # Course assignments
    am_course = models.ForeignKey(Course, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    pm_course = models.ForeignKey(Course, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    full_day_course = models.ForeignKey(Course, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    
    # Metrics
    satisfaction_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.student} in {self.schedule}"



class SchedulerConfig(models.Model):
    """
    Configuration for the scheduler algorithm
    Equivalent to the Config struct in Go code
    """
    name = models.CharField(max_length=255)
    iterations = models.IntegerField(default=1000)
    min_course_fill = models.FloatField(default=0.75)
    early_stop_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Config: {self.name}"
