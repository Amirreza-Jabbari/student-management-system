# Generated by Django 5.1.1 on 2024-11-09 17:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("student_management_app", "0006_alter_customuser_first_name"),
    ]

    operations = [
        migrations.RenameField(
            model_name="notificationstaffs",
            old_name="stafff_id",
            new_name="staff_id",
        ),
    ]
