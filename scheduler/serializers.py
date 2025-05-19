from rest_framework import serializers
from .models import Course, Student, Section, Schedule, ScheduleSnapshot, SchedulerConfig

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'name', 'time_slot', 'max_students', 'created_at', 'updated_at']

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = [
            'id', 'first_name', 'last_name', 'email', 'grade', 'priority',
            'am_preferences', 'pm_preferences', 'am_course', 'pm_course', 
            'full_day_course', 'created_at', 'updated_at'
        ]
    
    # Custom representation of course fields
    am_course = serializers.SerializerMethodField()
    pm_course = serializers.SerializerMethodField()
    full_day_course = serializers.SerializerMethodField()
    
    def get_am_course(self, obj):
        return obj.am_course.name if obj.am_course else None
    
    def get_pm_course(self, obj):
        return obj.pm_course.name if obj.pm_course else None
    
    def get_full_day_course(self, obj):
        return obj.full_day_course.name if obj.full_day_course else None

class SectionSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.name')
    time_slot = serializers.CharField(source='course.time_slot')
    enrolled_students_count = serializers.IntegerField(read_only=True)
    students = serializers.SerializerMethodField()
    
    class Meta:
        model = Section
        fields = ['id', 'course_name', 'time_slot', 'max_students', 'enrolled_students_count', 'students']
    
    def get_students(self, obj):
        return StudentSerializer(obj.get_students(), many=True).data

class ScheduleSnapshotSerializer(serializers.ModelSerializer):
    student = serializers.SerializerMethodField()
    am_course = serializers.SerializerMethodField()
    pm_course = serializers.SerializerMethodField()
    full_day_course = serializers.SerializerMethodField()
    
    class Meta:
        model = ScheduleSnapshot
        fields = ['id', 'student', 'am_course', 'pm_course', 'full_day_course', 'satisfaction_score']
    
    def get_student(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"
    
    def get_am_course(self, obj):
        return obj.am_course.name if obj.am_course else None
    
    def get_pm_course(self, obj):
        return obj.pm_course.name if obj.pm_course else None
    
    def get_full_day_course(self, obj):
        return obj.full_day_course.name if obj.full_day_course else None

class ScheduleSerializer(serializers.ModelSerializer):
    snapshots = ScheduleSnapshotSerializer(many=True, read_only=True)
    
    class Meta:
        model = Schedule
        fields = ['id', 'name', 'score', 'is_best', 'created_at', 'snapshots']

class SchedulerConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchedulerConfig
        fields = ['id', 'name', 'iterations', 'min_course_fill', 'early_stop_score', 'created_at', 'updated_at']

class RequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    grade = serializers.CharField()
    am_fd1 = serializers.CharField(required=False, allow_blank=True)
    am_fd2 = serializers.CharField(required=False, allow_blank=True)
    am_fd3 = serializers.CharField(required=False, allow_blank=True)
    am_fd4 = serializers.CharField(required=False, allow_blank=True)
    am_fd5 = serializers.CharField(required=False, allow_blank=True)
    pm1 = serializers.CharField(required=False, allow_blank=True)
    pm2 = serializers.CharField(required=False, allow_blank=True)
    pm3 = serializers.CharField(required=False, allow_blank=True)
    pm4 = serializers.CharField(required=False, allow_blank=True)
    pm5 = serializers.CharField(required=False, allow_blank=True)
    
    def get_am_courses(self):
        return [
            self.validated_data.get('am_fd1', ''),
            self.validated_data.get('am_fd2', ''),
            self.validated_data.get('am_fd3', ''),
            self.validated_data.get('am_fd4', ''),
            self.validated_data.get('am_fd5', ''),
        ]
    
    def get_pm_courses(self):
        return [
            self.validated_data.get('pm1', ''),
            self.validated_data.get('pm2', ''),
            self.validated_data.get('pm3', ''),
            self.validated_data.get('pm4', ''),
            self.validated_data.get('pm5', ''),
        ]
