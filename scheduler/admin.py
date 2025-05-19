from django.contrib import admin
from .models import Course, Student, Section, Schedule, ScheduleSnapshot, SchedulerConfig

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'time_slot', 'max_students')
    list_filter = ('time_slot',)
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'grade', 'priority', 'am_course', 'pm_course', 'full_day_course')
    list_filter = ('grade', 'priority')
    search_fields = ('first_name', 'last_name', 'email')
    ordering = ('last_name', 'first_name')

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('course', 'enrolled_students_count', 'max_students')
    list_filter = ('course__time_slot',)
    search_fields = ('course__name',)
    ordering = ('course__name',)
    
    def enrolled_students_count(self, obj):
        return obj.get_students().count()
    
    def max_students(self, obj):
        return obj.course.max_students
    
    enrolled_students_count.short_description = 'Enrolled Students'
    max_students.short_description = 'Maximum Students'

class ScheduleSnapshotInline(admin.TabularInline):
    model = ScheduleSnapshot
    extra = 0
    fields = ('student', 'am_course', 'pm_course', 'full_day_course', 'satisfaction_score')
    readonly_fields = ('student', 'am_course', 'pm_course', 'full_day_course', 'satisfaction_score')
    can_delete = False
    max_num = 0
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('name', 'score', 'is_best', 'created_at')
    list_filter = ('is_best',)
    search_fields = ('name',)
    ordering = ('-created_at',)
    readonly_fields = ('score', 'created_at')
    inlines = [ScheduleSnapshotInline]
    actions = ['mark_as_best']
    
    def mark_as_best(self, request, queryset):
        # Update all schedules to not be the best
        Schedule.objects.all().update(is_best=False)
        
        # Mark the selected schedule as the best
        queryset.update(is_best=True)
        
        self.message_user(request, f"Selected schedule marked as best. Other schedules are no longer marked as best.")
    
    mark_as_best.short_description = "Mark selected schedule as the best"

@admin.register(SchedulerConfig)
class SchedulerConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'iterations', 'min_course_fill', 'early_stop_score', 'created_at')
    search_fields = ('name',)
    ordering = ('-created_at',)
