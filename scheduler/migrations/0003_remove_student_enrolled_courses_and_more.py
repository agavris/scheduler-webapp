# Generated by Django 5.2.1 on 2025-05-16 03:26

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("scheduler", "0002_course_active_course_allow_multiple_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="student",
            name="enrolled_courses",
        ),
        migrations.AlterUniqueTogether(
            name="periodenrollmentsnapshot",
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name="periodenrollmentsnapshot",
            name="course",
        ),
        migrations.RemoveField(
            model_name="periodenrollmentsnapshot",
            name="snapshot",
        ),
        migrations.AlterUniqueTogether(
            name="course",
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name="schedule",
            name="academic_year",
        ),
        migrations.RemoveField(
            model_name="schedule",
            name="algorithm_used",
        ),
        migrations.RemoveField(
            model_name="schedule",
            name="execution_time",
        ),
        migrations.RemoveField(
            model_name="schedule",
            name="is_active",
        ),
        migrations.RemoveField(
            model_name="schedule",
            name="is_final",
        ),
        migrations.RemoveField(
            model_name="schedule",
            name="iterations",
        ),
        migrations.RemoveField(
            model_name="schedule",
            name="partial_count",
        ),
        migrations.RemoveField(
            model_name="schedule",
            name="perfect_count",
        ),
        migrations.RemoveField(
            model_name="schedule",
            name="school_type",
        ),
        migrations.RemoveField(
            model_name="schedule",
            name="semester",
        ),
        migrations.RemoveField(
            model_name="schedule",
            name="unsatisfied_count",
        ),
        migrations.RemoveField(
            model_name="schedule",
            name="updated_at",
        ),
        migrations.RemoveField(
            model_name="schedulesnapshot",
            name="school_type",
        ),
        migrations.RemoveField(
            model_name="student",
            name="active",
        ),
        migrations.RemoveField(
            model_name="student",
            name="completed_courses",
        ),
        migrations.RemoveField(
            model_name="student",
            name="gpa",
        ),
        migrations.RemoveField(
            model_name="student",
            name="parent_email",
        ),
        migrations.RemoveField(
            model_name="student",
            name="parent_name",
        ),
        migrations.RemoveField(
            model_name="student",
            name="parent_phone",
        ),
        migrations.RemoveField(
            model_name="student",
            name="period_preferences",
        ),
        migrations.RemoveField(
            model_name="student",
            name="required_courses",
        ),
        migrations.RemoveField(
            model_name="student",
            name="school_type",
        ),
        migrations.RemoveField(
            model_name="student",
            name="special_needs",
        ),
        migrations.RemoveField(
            model_name="student",
            name="student_id",
        ),
        migrations.RemoveField(
            model_name="student",
            name="unavailable_periods",
        ),
        migrations.AlterField(
            model_name="course",
            name="max_students",
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="course",
            name="name",
            field=models.CharField(max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name="course",
            name="time_slot",
            field=models.CharField(
                choices=[
                    ("AM", "Morning"),
                    ("PM", "Afternoon"),
                    ("FullDay", "Full Day"),
                ],
                max_length=10,
            ),
        ),
        migrations.AlterField(
            model_name="schedule",
            name="is_best",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="student",
            name="am_preferences",
            field=models.JSONField(default=list),
        ),
        migrations.AlterField(
            model_name="student",
            name="pm_preferences",
            field=models.JSONField(default=list),
        ),
        migrations.DeleteModel(
            name="Enrollment",
        ),
        migrations.DeleteModel(
            name="PeriodEnrollmentSnapshot",
        ),
        migrations.RemoveField(
            model_name="course",
            name="description",
        ),
        migrations.RemoveField(
            model_name="course",
            name="grade_level",
        ),
        migrations.RemoveField(
            model_name="course",
            name="grade_level_max",
        ),
        migrations.RemoveField(
            model_name="course",
            name="min_students",
        ),
        migrations.RemoveField(
            model_name="course",
            name="period",
        ),
        migrations.RemoveField(
            model_name="course",
            name="room",
        ),
        migrations.RemoveField(
            model_name="course",
            name="school_type",
        ),
        migrations.RemoveField(
            model_name="course",
            name="subject",
        ),
        migrations.RemoveField(
            model_name="course",
            name="teacher",
        ),
    ]
