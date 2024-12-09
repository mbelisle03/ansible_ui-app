# forms.py
from django import forms
from .models import Playbook, Inventory, Job

class PlaybookForm(forms.ModelForm):
    class Meta:
        model = Playbook
        fields = ['name', 'file']

class InventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ['name', 'description', 'file']
        

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['name', 'playbook', 'inventory']
        widgets = {
            'playbook': forms.Select(attrs={'class': 'form-control'}),
            'inventory': forms.Select(attrs={'class': 'form-control'}),
        }
