"""
Django Management Commands for Scheduler Tasks
Create these files in your Django app's management/commands/ directory
"""

# File: management/commands/run_scheduler_task.py
"""
Django management command to run scheduler tasks
Usage: python manage.py run_scheduler_task <task_name>
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from scheduler.tasks import run_task, get_task_status, SCHEDULED_TASKS


class Command(BaseCommand):
    help = 'Run scheduled tasks manually'

    def add_arguments(self, parser):
        parser.add_argument(
            'task_name',
            nargs='?',
            type=str,
            help='Name of the task to run (optional, shows available tasks if not provided)'
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='List all available tasks'
        )
        parser.add_argument(
            '--status',
            action='store_true',
            help='Show task status information'
        )

    def handle(self, *args, **options):
        if options['list'] or options['status']:
            self.show_task_info()
            return
        
        task_name = options['task_name']
        
        if not task_name:
            self.show_task_info()
            return
        
        if task_name not in SCHEDULED_TASKS:
            self.stdout.write(
                self.style.ERROR(f'Task "{task_name}" not found.')
            )
            self.show_available_tasks()
            return
        
        self.stdout.write(
            self.style.WARNING(f'Running task: {task_name}...')
        )
        
        start_time = timezone.now()
        result = run_task(task_name)
        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()
        
        if result['success']:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Task "{task_name}" completed successfully in {duration:.2f} seconds'
                )
            )
            if 'message' in result:
                self.stdout.write(f'Result: {result["message"]}')
            if 'results' in result:
                self.stdout.write(f'Details: {result["results"]}')
        else:
            self.stdout.write(
                self.style.ERROR(
                    f'❌ Task "{task_name}" failed: {result.get("error", "Unknown error")}'
                )
            )
    
    def show_task_info(self):
        status = get_task_status()
        
        self.stdout.write(
            self.style.SUCCESS(f'📋 Available Scheduler Tasks ({status["total_tasks"]} total)')
        )
        self.stdout.write('')
        
        for name, info in status['tasks'].items():
            self.stdout.write(f'🔹 {name}')
            self.stdout.write(f'   Schedule: {info["schedule"]}')
            self.stdout.write(f'   Description: {info["description"]}')
            self.stdout.write('')
        
        self.stdout.write(
            self.style.WARNING('Usage: python manage.py run_scheduler_task <task_name>')
        )
    
    def show_available_tasks(self):
        self.stdout.write(self.style.WARNING('Available tasks:'))
        for task_name in SCHEDULED_TASKS.keys():
            self.stdout.write(f'  - {task_name}')


# File: management/commands/setup_cron_jobs.py
"""
Django management command to generate cron job configuration
Usage: python manage.py setup_cron_jobs
"""


# File: scheduler_config.py
"""
Configuration file for scheduler settings
"""

from django.conf import settings
import os

# Scheduler configuration
SCHEDULER_CONFIG = {
    'EMAIL_NOTIFICATIONS': {
        'enabled': True,
        'from_email': getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@healthcare.com'),
        'admin_emails': getattr(settings, 'ADMIN_EMAILS', []),
    },
    
    'SMS_NOTIFICATIONS': {
        'enabled': False,  # Set to True when SMS service is configured
        'provider': 'twilio',  # or 'local_gateway'
        'api_key': os.environ.get('SMS_API_KEY'),
        'api_secret': os.environ.get('SMS_API_SECRET'),
    },
    
    'TASK_SETTINGS': {
        'reminder_hours_ahead': 24,  # Send reminders 24 hours before appointment
        'max_retry_attempts': 3,
        'retry_delay_minutes': 5,
        'timeout_minutes': 30,
    },
    
    'LOG_SETTINGS': {
        'log_file': '/var/log/healthcare_scheduler.log',
        'log_level': 'INFO',
        'max_log_size_mb': 100,
        'backup_count': 5,
    },
    
    'HEALTH_CHECK': {
        'enabled': True,
        'alert_on_failure': True,
        'critical_systems': ['database_connection', 'appointment_system'],
    },
    
    'DATA_RETENTION': {
        'keep_logs_days': 90,
        'keep_expired_tokens_days': 30,
        'cleanup_frequency': 'weekly',
    }
}

# Celery configuration (if using Celery)
CELERY_CONFIG = {
    'broker_url': os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    'result_backend': os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    'task_serializer': 'json',
    'accept_content': ['json'],
    'result_serializer': 'json',
    'timezone': 'Asia/Dhaka',
    'enable_utc': True,
    
    # Task routing
    'task_routes': {
        'scheduler.tasks.send_appointment_reminders': {'queue': 'notifications'},
        'scheduler.tasks.generate_monthly_reports': {'queue': 'reports'},
        'scheduler.tasks.system_health_check': {'queue': 'monitoring'},
    },
    
    # Beat schedule (for Celery Beat)
    'beat_schedule': {
        'send-appointment-reminders': {
            'task': 'scheduler.tasks.send_appointment_reminders',
            'schedule': 60.0 * 60 * 24,  # Daily
            'options': {'queue': 'notifications'}
        },
        'generate-monthly-reports': {
            'task': 'scheduler.tasks.generate_monthly_reports',
            'schedule': 60.0 * 60 * 24 * 30,  # Monthly (approximate)
            'options': {'queue': 'reports'}
        },
        'system-health-check': {
            'task': 'scheduler.tasks.system_health_check',
            'schedule': 60.0 * 60,  # Hourly
            'options': {'queue': 'monitoring'}
        },
        'cleanup-old-data': {
            'task': 'scheduler.tasks.cleanup_old_data',
            'schedule': 60.0 * 60 * 24 * 7,  # Weekly
            'options': {'queue': 'maintenance'}
        },
    },
}


# File: celery_tasks.py (Optional - for Celery integration)
"""
Celery task definitions
Use this if you prefer Celery over cron jobs
"""



# File: docker-compose.scheduler.yml (Optional - for Docker deployment)
"""
Docker Compose configuration for scheduler services
"""

DOCKER_COMPOSE_SCHEDULER = '''
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  celery_worker:
    build: .
    command: celery -A healthcare_project worker --loglevel=info --queues=notifications,reports,monitoring,maintenance
    depends_on:
      - redis
      - db
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    volumes:
      - .:/app
      - /var/log:/var/log

  celery_beat:
    build: .
    command: celery -A healthcare_project beat --loglevel=info
    depends_on:
      - redis
      - db
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    volumes:
      - .:/app

  flower:
    build: .
    command: celery -A healthcare_project flower --port=5555
    depends_on:
      - redis
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    ports:
      - "5555:5555"

volumes:
  redis_data:
'''

# File: systemd_service.py (Optional - for systemd service)
"""
Generate systemd service files for scheduler
"""

SYSTEMD_SERVICE_TEMPLATE = '''
[Unit]
Description=Healthcare Management System Scheduler
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory={project_dir}
Environment=PATH={venv_path}/bin
Environment=DJANGO_SETTINGS_MODULE=healthcare_project.settings
ExecStart={venv_path}/bin/python {manage_py} run_scheduler_task {task_name}
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
'''

def generate_systemd_services(project_dir, venv_path):
    """Generate systemd service files"""
    manage_py = os.path.join(project_dir, 'manage.py')
    
    services = {
        'healthcare-reminders.service': 'send_appointment_reminders',
        'healthcare-reports.service': 'generate_monthly_reports',
        'healthcare-cleanup.service': 'cleanup_old_data',
        'healthcare-health.service': 'system_health_check',
    }
    
    for service_file, task_name in services.items():
        content = SYSTEMD_SERVICE_TEMPLATE.format(
            project_dir=project_dir,
            venv_path=venv_path,
            manage_py=manage_py,
            task_name=task_name
        )
        
        with open(service_file, 'w') as f:
            f.write(content)
        
        print(f"Generated {service_file}")
    
    print("\nTo install services:")
    print("sudo cp *.service /etc/systemd/system/")
    print("sudo systemctl daemon-reload")
    print("sudo systemctl enable healthcare-*.service")


# File: monitoring.py
"""
Monitoring and alerting utilities
"""

import logging
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime, timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)


class TaskMonitor:
    """Monitor task execution and send alerts"""
    
    def __init__(self):
        self.alerts_sent = {}
        self.alert_cooldown = timedelta(hours=1)  # Don't spam alerts
    
    def log_task_start(self, task_name: str):
        """Log task start"""
        logger.info(f"Task started: {task_name} at {timezone.now()}")
    
    def log_task_completion(self, task_name: str, success: bool, duration: float, result: dict):
        """Log task completion"""
        status = "SUCCESS" if success else "FAILED"
        logger.info(f"Task {status}: {task_name} completed in {duration:.2f}s")
        
        if not success:
            self.send_failure_alert(task_name, result.get('error', 'Unknown error'))
    
    def send_failure_alert(self, task_name: str, error: str):
        """Send alert for task failure"""
        # Check if we recently sent an alert for this task
        if task_name in self.alerts_sent:
            last_alert = self.alerts_sent[task_name]
            if timezone.now() - last_alert < self.alert_cooldown:
                return
        
        try:
            admin_emails = getattr(settings, 'ADMIN_EMAILS', [])
            if not admin_emails:
                return
            
            subject = f"🚨 Scheduler Task Failed: {task_name}"
            message = f"""
Task Failure Alert

Task: {task_name}
Failed at: {timezone.now().strftime('%Y-%m-%d %H:%M:%S %Z')}
Error: {error}

Please investigate the issue.

Healthcare Management System
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=admin_emails,
                fail_silently=True
            )
            
            self.alerts_sent[task_name] = timezone.now()
            logger.info(f"Failure alert sent for task: {task_name}")
            
        except Exception as e:
            logger.error(f"Failed to send failure alert: {str(e)}")


# Global task monitor instance
task_monitor = TaskMonitor()