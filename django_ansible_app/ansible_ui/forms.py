# forms.py
from django import forms
from .models import Playbook, Inventory

class PlaybookForm(forms.ModelForm):
    class Meta:
        model = Playbook
        fields = ['name', 'file']

class InventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ['name', 'description', 'file']