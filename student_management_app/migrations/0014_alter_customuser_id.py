# Generated by Django 5.1.1 on 2025-01-22 13:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "student_management_app",
            "0013_remove_staffattendance_session_year_id_and_more",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="customuser",
            name="id",
            field=models.BigAutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
    ]
