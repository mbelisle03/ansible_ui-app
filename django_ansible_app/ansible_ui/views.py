from django.shortcuts import render, redirect
from django.contrib.auth import views as auth_views
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.http import HttpResponse
from django.contrib import messages
from .forms import JobForm
from django import forms
from .models import Playbook
from .models import Inventory
from .models import Job
from .forms import PlaybookForm
from .forms import InventoryForm
from celery import shared_task
from celery.result import AsyncResult
from .tasks import execute_playbook, terminate_task, run_ansible_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import subprocess
import json

class CustomLoginView(auth_views.LoginView):
    template_name = 'login.html'

def form_invalid(self, form):
    messages.error(self.request, "Login failed. Please try again.")
    return super().form_invalid(form)
    
@login_required
def dashboard(request):
    return render(request, 'dashboard.html')

def playbook_list(request):
    playbooks = Playbook.objects.all()
    return render(request, 'playbooks/list.html', {'playbooks': playbooks})

def inventory_list(request):
    inventories = Inventory.objects.all()
    return render(request, 'inventories/list.html', {'inventories': inventories})

def inventory_upload(request):
    """
    View to upload a new inventory file.
    """
    if request.method == 'POST':
        form = InventoryForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('inventory_list')
    else:
        form = InventoryForm()
    return render(request, 'inventories/upload.html', {'form': form})

def job_list(request):
    jobs = Job.objects.all()  # Fetch all Job records from the database
    return render(request, 'jobs/list.html', {'jobs': jobs})

@login_required
def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    if request.method == 'POST':
        if job.task_id:
            result = terminate_task(job.task_id)
            messages.success(request, result)
        else:
            messages.error(request, 'No task ID found for this job.')
        return redirect('job_detail', job_id=job_id)  # Redirect to refresh the page
    return render(request, 'jobs/detail.html', {'job': job})


@login_required
def create_job(request):
    """
    View to create a new job by selecting a playbook and inventory.
    """
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)  # Create the job instance but don't save to the database yet
            
            # Start the Celery task and get the task_id
            task = run_ansible_task.delay(job.playbook.file.path, job.inventory.file.path, job.id)
            job.task_id = task.id  # Set the task_id
            
            job.save()  # Now save the job instance
            messages.success(request, 'Job created successfully.')
            return redirect('jobs_list')  # Redirect to the jobs list
        else:
            messages.error(request, 'There was an error creating the job. Please check the form.')
            print(form.errors)  # Print form errors to the console for debugging
    else:
        form = JobForm()
    return render(request, 'jobs/create.html', {'form': form})

@login_required
def execute_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    playbook_path = job.playbook.file.path
    inventory_path = job.inventory.file.path
    job.status = "In Progress"
    job.save()

    # Start the Celery task and fetch its response
    result = run_ansible_task.delay(playbook_path, inventory_path, job.id)
    messages.success(request, f"Execution of Job {job.id} started. Check back for the result.")

    # Redirect to the job detail page
    return redirect('job_detail', job_id=job_id)


def terminate_job_view(request, task_id):
    if request.method == 'POST':
        result = terminate_task(task_id)
        messages.success(request, result)
        return redirect('jobs_list')  # Redirect to your job list or another page

    return render(request, 'terminate_job.html', {'task_id': task_id})

def playbook_upload(request):
    if request.method == 'POST':
        form = PlaybookForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('playbook_list')
    else:
        form = PlaybookForm()
    return render(request, 'playbooks/upload.html', {'form': form})

class PlaybookEditForm(forms.ModelForm):
    class Meta:
        model = Playbook
        fields = ['name', 'description', 'file']  # Include fields you want to edit

@login_required
def edit_playbook(request, playbook_id):
    playbook = get_object_or_404(Playbook, id=playbook_id)
    
    if request.method == 'POST':
        form = PlaybookEditForm(request.POST, request.FILES, instance=playbook)
        if form.is_valid():
            form.save()
            messages.success(request, 'Playbook updated successfully.')
            return redirect('playbook_list')
    else:
        form = PlaybookEditForm(instance=playbook)
    
    return render(request, 'playbooks/edit.html', {'form': form, 'playbook': playbook})

@shared_task
def run_ansible_task(playbook_path, inventory_path, job_id):
    try:
        # Run the Ansible playbook command
        process = subprocess.Popen(
            ['ansible-playbook', playbook_path, '-i', inventory_path, '--extra-vars', 'ansible_python_interpreter=/usr/bin/python3'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()

        # Parse the JSON output from Ansible if possible
        output = {"stdout": stdout, "stderr": stderr}
        try:
            output["parsed"] = json.loads(stdout)
        except json.JSONDecodeError:
            output["parsed"] = "Failed to parse JSON from stdout."

        # Save output to the database (update the job instance)
        from .models import Job
        job = Job.objects.get(id=job_id)
        job.output = json.dumps(output, indent=2)  # Store the JSON output
        job.status = "Success" if process.returncode == 0 else "Failed"
        job.save()

        return output
    except Exception as e:
        return {"error": str(e)}

@login_required
def run_playbook(request, playbook_id):
    playbook = get_object_or_404(Playbook, id=playbook_id)
    inventory_path = '/media/inventories/inventory.txt'  # Update with your inventory file path
    playbook_path = playbook.file.path

    # Trigger the Celery task
    result = execute_playbook.delay(playbook_path, inventory_path)

    # Update last run time
    playbook.last_run_at = now()
    playbook.save()

    return render(request, 'playbooks/run_status.html', {'task_id': result.id})

def terminate_task(task_id):
    result = AsyncResult(task_id)
    if result.state in ['PENDING', 'STARTED']:
        result.revoke(terminate=True)
        try:
            job = Job.objects.get(task_id=task_id)
            job.status = "Terminated"
            job.save()
            return f"Task {task_id} terminated successfully."
        except Job.DoesNotExist:
            return f"No job found with task_id {task_id}."
    return f"Task {task_id} is in state {result.state} and cannot be terminated."