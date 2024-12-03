from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.http import HttpResponse
from django.contrib import messages
from .models import Playbook
from .models import Inventory
from .models import Job
from .forms import PlaybookForm
from .forms import InventoryForm
from celery import shared_task
from .tasks import execute_playbook
import subprocess

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
    """
    View to display details of a specific job.
    """
    # Retrieve the job instance or return a 404 error if not found
    job = get_object_or_404(Job, id=job_id)

    # Pass the job object to the template
    return render(request, 'jobs/detail.html', {'job': job})

@login_required
def create_job(request):
    """
    View to create a new job by selecting a playbook and inventory.
    """
    if request.method == 'POST':
        playbook_id = request.POST.get('playbook_id')
        inventory_id = request.POST.get('inventory_id')
        playbook = Playbook.objects.get(id=playbook_id)
        inventory = Inventory.objects.get(id=inventory_id)

        # Create the job with the selected playbook and inventory
        Job.objects.create(playbook=playbook, inventory=inventory)
        return redirect('jobs_list')

    playbooks = Playbook.objects.all()
    inventories = Inventory.objects.all()
    return render(request, 'jobs/create.html', {
        'playbooks': playbooks,
        'inventories': inventories
    })

@login_required
def execute_job(request, job_id):
    """
    View to execute a job using a Celery task.
    """
    job = Job.objects.get(id=job_id)

    # Trigger the Ansible playbook execution
    result = run_ansible_task.delay(job.playbook.file.path, job.inventory.file.path)

    # Update job status (Pending for now; Celery worker will update later)
    job.status = 'In Progress'
    job.save()

    messages.success(request, f"Job {job.id} is being executed.")
    return redirect('jobs_list')


def playbook_upload(request):
    if request.method == 'POST':
        form = PlaybookForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('playbook_list')
    else:
        form = PlaybookForm()
    return render(request, 'playbooks/upload.html', {'form': form})

@shared_task
def run_ansible_task(playbook_path, inventory_path):
    """
    Executes an Ansible playbook and returns the result.
    """
    result = subprocess.run(
        ['ansible-playbook', playbook_path, '-i', inventory_path],
        capture_output=True, text=True
    )
    return result.stdout

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