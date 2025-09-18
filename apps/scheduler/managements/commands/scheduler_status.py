from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import connection
from django.core.cache import cache
import subprocess
import sys

from scheduler.tasks import get_task_status


class Command(BaseCommand):
    help = "Check scheduler and system status"

    def add_arguments(self, parser):
        parser.add_argument(
            "--detailed", action="store_true", help="Show detailed system status"
        )
        parser.add_argument("--cron", action="store_true", help="Check cron job status")

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS("🏥 Healthcare Management System - Scheduler Status")
        )
        self.stdout.write("=" * 60)

        # Show task information
        self.show_task_status()

        if options["detailed"]:
            self.show_detailed_status()

        if options["cron"]:
            self.show_cron_status()

    def show_task_status(self):
        """Show scheduled task status"""
        self.stdout.write("")
        self.stdout.write(self.style.WARNING("📋 Scheduled Tasks Status"))
        self.stdout.write("-" * 30)

        status = get_task_status()

        for name, info in status["tasks"].items():
            self.stdout.write(f"🔹 {name}")
            self.stdout.write(f'   Schedule: {info["schedule"]}')
            self.stdout.write(f'   Description: {info["description"]}')
            self.stdout.write("")

        self.stdout.write(f'Total Tasks: {status["total_tasks"]}')
        self.stdout.write(f'Last Check: {status["last_check"]}')

    def show_detailed_status(self):
        """Show detailed system status"""
        self.stdout.write("")
        self.stdout.write(self.style.WARNING("🔍 Detailed System Status"))
        self.stdout.write("-" * 30)

        # Database status
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            self.stdout.write("✅ Database: Connected")
        except Exception as e:
            self.stdout.write(f"❌ Database: Error - {str(e)}")

        # Cache status
        try:
            cache.set("status_check", "ok", 30)
            if cache.get("status_check") == "ok":
                self.stdout.write("✅ Cache: Working")
            else:
                self.stdout.write("❌ Cache: Not responding")
        except Exception as e:
            self.stdout.write(f"❌ Cache: Error - {str(e)}")

        # Python environment
        self.stdout.write(f"🐍 Python Version: {sys.version.split()[0]}")
        self.stdout.write(
            f'🕐 Current Time: {timezone.now().strftime("%Y-%m-%d %H:%M:%S %Z")}'
        )

    def show_cron_status(self):
        """Show cron job status"""
        self.stdout.write("")
        self.stdout.write(self.style.WARNING("⏰ Cron Jobs Status"))
        self.stdout.write("-" * 30)

        try:
            result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)

            if result.returncode == 0:
                cron_output = result.stdout
                healthcare_jobs = [
                    line
                    for line in cron_output.split("\n")
                    if "run_scheduler_task" in line and not line.strip().startswith("#")
                ]

                if healthcare_jobs:
                    self.stdout.write(
                        f"✅ Found {len(healthcare_jobs)} healthcare cron jobs:"
                    )
                    for job in healthcare_jobs:
                        self.stdout.write(f"   {job.strip()}")
                else:
                    self.stdout.write("⚠️  No healthcare cron jobs found")
            else:
                self.stdout.write("❌ Cannot access crontab")

        except Exception as e:
            self.stdout.write(f"❌ Error checking cron jobs: {str(e)}")
