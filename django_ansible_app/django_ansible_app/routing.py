# routing.py

from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/job/<int:job_id>/', consumers.JobConsumer.as_asgi()),
]