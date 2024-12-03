from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_ansible_app.settings')

# Create the Celery app instance.
app = Celery('django_ansible_app')

# Load settings from Django's settings module using a namespace.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscover tasks in installed apps.
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
