import subprocess
from celery import shared_task
from celery.result import AsyncResult
from .models import Job
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import signal


@shared_task
def execute_playbook(playbook_path, inventory_path):
    """
    Executes an Ansible playbook.
    """
    try:
        result = subprocess.run(
            ['ansible-playbook', playbook_path, '-i', inventory_path],
            capture_output=True, text=True
        )
        return {
            'status': 'success',
            'stdout': result.stdout,
            'stderr': result.stderr
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }

@shared_task
def run_ansible_task(playbook_path, inventory_path, job_id):
    channel_layer = get_channel_layer()
    process = subprocess.Popen(
        ['ansible-playbook', playbook_path, '-i', inventory_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    for line in process.stdout:
        async_to_sync(channel_layer.group_send)(
            f'job_{job_id}',
            {
                'type': 'send_job_output',
                'output': line.strip()
            }
        )

    process.stdout.close()
    process.wait()

    # Update the job status in the database after completion
    job = Job.objects.get(id=job_id)
    if process.returncode == 0:
        job.status = 'Success'
    else:
        job.status = 'Failed'
    job.save()

@shared_task(bind=True)
def long_running_task(self):
    def handle_signal(signum, frame):
        print("Termination signal received. Cleaning up...")
        # Perform any cleanup actions here
        self.update_state(state='TERMINATED')

    # Register the signal handler
    signal.signal(signal.SIGTERM, handle_signal)
    
def terminate_task(task_id):
    # Get the task result using the task ID
    task_result = AsyncResult(task_id)

    # Check if the task is currently running
    if task_result.state in ['PENDING', 'STARTED']:
        # Revoke the task and terminate it
        task_result.revoke(terminate=True)
        return f'Task {task_id} has been terminated.'
    else:
        return f'Task {task_id} is not running or has already completed.'