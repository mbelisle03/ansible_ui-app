from django.db import models
from django.utils.timezone import now

# Create your models here.
# models.py
from django.db import models

class Playbook(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='playbooks/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    last_run_at = models.DateTimeField(null=True, blank=True)

class Inventory(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='inventories/')
    created_at = models.DateTimeField(auto_now_add=True)

class Job(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Success', 'Success'),
        ('Failed', 'Failed'),
    ]

    playbook = models.ForeignKey(Playbook, on_delete=models.CASCADE, related_name='jobs')
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name='jobs')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    executed_at = models.DateTimeField(default=now)
    output = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'Job {self.id} - {self.playbook.name}'