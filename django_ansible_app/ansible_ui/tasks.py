import subprocess
from celery import shared_task

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
def run_ansible_task(playbook_path, inventory_path):
    """
    Executes an Ansible playbook with the specified inventory and returns the result.
    """
    result = subprocess.run(
        ['ansible-playbook', playbook_path, '-i', inventory_path],
        capture_output=True, text=True
    )
    return result.stdout
