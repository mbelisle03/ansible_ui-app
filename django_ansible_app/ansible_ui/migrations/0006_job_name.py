# Generated by Django 5.1.3 on 2024-12-04 03:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ansible_ui', '0005_job_inventory'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='name',
            field=models.CharField(blank=True, max_length=255, unique=True),
        ),
    ]