# Generated by Django 5.1.1 on 2024-11-09 17:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("student_management_app", "0007_rename_stafff_id_notificationstaffs_staff_id"),
    ]

    operations = [
        migrations.RenameField(
            model_name="notificationstaffs",
            old_name="staff_id",
            new_name="stafff_id",
        ),
    ]
