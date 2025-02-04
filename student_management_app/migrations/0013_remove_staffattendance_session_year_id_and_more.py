# Generated by Django 5.1.1 on 2025-01-20 20:52

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("student_management_app", "0012_alter_students_gender_staffattendance"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="staffattendance",
            name="session_year_id",
        ),
        migrations.AlterField(
            model_name="staffattendance",
            name="staff_id",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="student_management_app.staffs",
            ),
        ),
    ]
