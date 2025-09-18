import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from account.models import User
from account.services import UserServices
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q
from django.utils import timezone

from apps.appointment.models import Appointment
from apps.appointment.services import AppointmentServices
from apps.report.services import ReportServices

# For Celery integration (uncomment if using Celery)
# from celery import shared_task


logger = logging.getLogger(__name__)


class NotificationService:
    """Service for handling various types of notifications"""

    @staticmethod
    def send_appointment_reminder_email(
        patient_email: str,
        patient_name: str,
        doctor_name: str,
        appointment_datetime: datetime,
        consultation_fee: float,
        notes: str = "",
    ) -> bool:
        """
        Send appointment reminder email to patient
        """
        try:
            subject = f'Appointment Reminder - Tomorrow at {appointment_datetime.strftime("%I:%M %p")}'

            message = f"""
Dear {patient_name},

This is a friendly reminder about your upcoming appointment:

📅 Date: {appointment_datetime.strftime("%A, %B %d, %Y")}
🕐 Time: {appointment_datetime.strftime("%I:%M %p")}
👨‍⚕️ Doctor: {doctor_name}
💰 Consultation Fee: ৳{consultation_fee}

{f"Notes: {notes}" if notes else ""}

Please arrive 10 minutes early for your appointment.

If you need to reschedule or cancel, please contact us as soon as possible.

Best regards,
Healthcare Management Team

---
This is an automated reminder. Please do not reply to this email.
            """

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[patient_email],
                fail_silently=False,
            )

            logger.info(f"Appointment reminder email sent to {patient_email}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to send appointment reminder email to {patient_email}: {str(e)}"
            )
            return False

    @staticmethod
    def send_sms_reminder(
        mobile: str, patient_name: str, doctor_name: str, appointment_datetime: datetime
    ) -> bool:
        """
        Send SMS reminder (placeholder for SMS service integration)
        """
        try:
            # Placeholder for SMS service integration (Twilio, local SMS gateway, etc.)
            message = f"""
Hi {patient_name}, reminder: You have an appointment with {doctor_name} tomorrow at {appointment_datetime.strftime("%I:%M %p")}. 
Please arrive 10 minutes early. Contact us to reschedule if needed.
            """

            # TODO: Integrate with SMS service
            logger.info(f"SMS reminder sent to {mobile}: {message.strip()}")
            return True

        except Exception as e:
            logger.error(f"Failed to send SMS reminder to {mobile}: {str(e)}")
            return False

    @staticmethod
    def send_monthly_report_notification(
        doctor_email: str, doctor_name: str, report_period: str, report_summary: Dict
    ) -> bool:
        """
        Send monthly report notification to doctor
        """
        try:
            subject = f"Your Monthly Report - {report_period}"

            message = f"""
Dear Dr. {doctor_name},

Your monthly practice report for {report_period} is now available.

📊 Summary:
• Total Appointments: {report_summary.get('total_appointments', 0)}
• Completed Appointments: {report_summary.get('completed_appointments', 0)}
• Total Earnings: ৳{report_summary.get('total_earnings', 0):,.2f}
• Unique Patients: {report_summary.get('unique_patients', 0)}
• Completion Rate: {report_summary.get('completion_rate', 0):.1f}%

You can view your detailed report by logging into your dashboard.

Best regards,
Healthcare Management Team
            """

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[doctor_email],
                fail_silently=False,
            )

            logger.info(f"Monthly report notification sent to {doctor_email}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to send monthly report notification to {doctor_email}: {str(e)}"
            )
            return False


# Task Functions (can be decorated with @shared_task for Celery)
def send_appointment_reminders():
    """
    Send appointment reminders for appointments scheduled 24 hours from now
    Should be run daily (recommended time: 9:00 AM)
    """
    try:
        logger.info("Starting appointment reminder task")

        # Get appointments scheduled for tomorrow (24 hours ahead)
        reminders = AppointmentServices.get_appointment_reminders(hours_ahead=24)

        if not reminders:
            logger.info("No appointment reminders to send")
            return {"success": True, "sent": 0, "failed": 0}

        sent_count = 0
        failed_count = 0

        for reminder in reminders:
            try:
                # Send email reminder
                email_sent = NotificationService.send_appointment_reminder_email(
                    patient_email=reminder["patient_email"],
                    patient_name=reminder["patient_name"],
                    doctor_name=reminder["doctor_name"],
                    appointment_datetime=reminder["appointment_datetime"],
                    consultation_fee=reminder["consultation_fee"],
                    notes=reminder["notes"],
                )

                # Send SMS reminder (if mobile number available)
                sms_sent = False
                if reminder["patient_mobile"]:
                    sms_sent = NotificationService.send_sms_reminder(
                        mobile=reminder["patient_mobile"],
                        patient_name=reminder["patient_name"],
                        doctor_name=reminder["doctor_name"],
                        appointment_datetime=reminder["appointment_datetime"],
                    )

                if email_sent or sms_sent:
                    sent_count += 1
                    logger.info(
                        f"Reminder sent for appointment {reminder['appointment_id']}"
                    )
                else:
                    failed_count += 1
                    logger.warning(
                        f"Failed to send reminder for appointment {reminder['appointment_id']}"
                    )

            except Exception as e:
                failed_count += 1
                logger.error(
                    f"Error sending reminder for appointment {reminder['appointment_id']}: {str(e)}"
                )

        logger.info(
            f"Appointment reminder task completed: {sent_count} sent, {failed_count} failed"
        )

        return {
            "success": True,
            "total_reminders": len(reminders),
            "sent": sent_count,
            "failed": failed_count,
        }

    except Exception as e:
        logger.error(f"Error in appointment reminder task: {str(e)}")
        return {"success": False, "error": str(e)}


def generate_monthly_reports():
    """
    Generate monthly reports for all doctors
    Should be run on the 1st of each month (recommended time: 2:00 AM)
    """
    try:
        logger.info("Starting monthly report generation task")

        # Calculate previous month
        current_date = timezone.now()
        if current_date.month == 1:
            prev_month = 12
            prev_year = current_date.year - 1
        else:
            prev_month = current_date.month - 1
            prev_year = current_date.year

        # Generate reports for all doctors who had appointments
        result = ReportServices.bulk_generate_monthly_reports(prev_year, prev_month)

        if result["success"]:
            # Send notifications to doctors about their reports
            notify_doctors_about_reports(prev_year, prev_month, result["results"])

            logger.info(f"Monthly report generation completed: {result['message']}")
            return result
        else:
            logger.error(f"Monthly report generation failed: {result['message']}")
            return result

    except Exception as e:
        logger.error(f"Error in monthly report generation task: {str(e)}")
        return {"success": False, "error": str(e)}


def notify_doctors_about_reports(year: int, month: int, generation_results: Dict):
    """
    Notify doctors about their generated monthly reports
    """
    try:
        import calendar

        period_name = f"{calendar.month_name[month]} {year}"

        successful_reports = [
            r for r in generation_results["results"] if r["status"] == "success"
        ]

        for report_result in successful_reports:
            doctor_id = report_result["doctor_id"]

            # Get doctor info
            from account.selectors import DoctorSelector

            doctor = DoctorSelector.get_doctor_by_id(doctor_id)
            if not doctor:
                continue

            # Get report summary
            from report.selectors import ReportSelector

            report = ReportSelector.get_doctor_monthly_report(doctor_id, year, month)
            if not report:
                continue

            # Extract summary data
            report_data = report.report_data
            summary = {
                "total_appointments": report_data["appointment_stats"][
                    "total_appointments"
                ],
                "completed_appointments": report_data["appointment_stats"][
                    "completed_appointments"
                ],
                "total_earnings": report_data["financial_stats"]["total_earnings"],
                "unique_patients": report_data["patient_stats"]["unique_patients"],
                "completion_rate": report_data["appointment_stats"]["completion_rate"],
            }

            # Send notification
            NotificationService.send_monthly_report_notification(
                doctor_email=doctor.email,
                doctor_name=doctor.full_name,
                report_period=period_name,
                report_summary=summary,
            )

        logger.info(f"Report notifications sent to {len(successful_reports)} doctors")

    except Exception as e:
        logger.error(f"Error sending report notifications: {str(e)}")


def cleanup_old_data():
    """
    Clean up old data and perform maintenance tasks
    Should be run weekly (recommended: Sunday at 3:00 AM)
    """
    try:
        logger.info("Starting data cleanup task")

        cleanup_results = {
            "expired_tokens_cleaned": 0,
            "old_logs_cleaned": 0,
            "cache_cleared": False,
        }

        # 1. Clean up expired JWT tokens (if using token blacklist)
        try:
            from rest_framework_simplejwt.token_blacklist.models import (
                BlacklistedToken,
                OutstandingToken,
            )

            # Remove tokens older than 30 days
            cutoff_date = timezone.now() - timedelta(days=30)
            expired_tokens = BlacklistedToken.objects.filter(
                token__created_at__lt=cutoff_date
            )
            expired_count = expired_tokens.count()
            expired_tokens.delete()

            cleanup_results["expired_tokens_cleaned"] = expired_count
            logger.info(f"Cleaned up {expired_count} expired tokens")

        except ImportError:
            logger.info("JWT token blacklist not available, skipping token cleanup")

        # 2. Clean up old log entries (if you have a logging model)
        # This is optional based on your logging strategy

        # 3. Clear old cache entries
        try:
            from django.core.cache import cache

            cache.clear()
            cleanup_results["cache_cleared"] = True
            logger.info("Cache cleared successfully")
        except Exception as e:
            logger.warning(f"Failed to clear cache: {str(e)}")

        # 4. Update appointment statuses (mark past pending appointments as missed)
        try:
            past_appointments = Appointment.objects.filter(
                appointment_date__lt=timezone.now().date(),
                status__in=[Appointment.PENDING, Appointment.CONFIRMED],
            )

            # Mark as completed or missed based on business logic
            # For now, we'll leave them as-is since doctors should manually update status

        except Exception as e:
            logger.warning(f"Failed to update appointment statuses: {str(e)}")

        logger.info(f"Data cleanup completed: {cleanup_results}")
        return {"success": True, "results": cleanup_results}

    except Exception as e:
        logger.error(f"Error in data cleanup task: {str(e)}")
        return {"success": False, "error": str(e)}


def system_health_check():
    """
    Perform system health checks and send alerts if needed
    Should be run every hour
    """
    try:
        logger.info("Starting system health check")

        health_status = {
            "database_connection": False,
            "cache_connection": False,
            "email_service": False,
            "appointment_system": False,
            "report_system": False,
            "errors": [],
        }

        # 1. Check database connection
        try:
            from django.db import connection

            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            health_status["database_connection"] = True
        except Exception as e:
            health_status["errors"].append(f"Database connection failed: {str(e)}")

        # 2. Check cache connection
        try:
            from django.core.cache import cache

            cache.set("health_check", "ok", 30)
            if cache.get("health_check") == "ok":
                health_status["cache_connection"] = True
        except Exception as e:
            health_status["errors"].append(f"Cache connection failed: {str(e)}")

        # 3. Check email service
        try:
            # Simple email test (won't actually send)
            from django.core.mail import get_connection

            connection = get_connection()
            connection.open()
            connection.close()
            health_status["email_service"] = True
        except Exception as e:
            health_status["errors"].append(f"Email service failed: {str(e)}")

        # 4. Check appointment system
        try:
            # Test appointment query
            recent_appointments = Appointment.objects.filter(
                created_at__gte=timezone.now() - timedelta(hours=24)
            ).count()
            health_status["appointment_system"] = True
        except Exception as e:
            health_status["errors"].append(f"Appointment system failed: {str(e)}")

        # 5. Check report system
        try:
            # Test report generation
            ReportServices.get_report_statistics()
            health_status["report_system"] = True
        except Exception as e:
            health_status["errors"].append(f"Report system failed: {str(e)}")

        # Send alert if critical systems are down
        critical_systems = ["database_connection", "appointment_system"]
        critical_failures = [sys for sys in critical_systems if not health_status[sys]]

        if critical_failures:
            send_system_alert(health_status, critical_failures)

        logger.info(f"System health check completed: {health_status}")
        return {"success": True, "health_status": health_status}

    except Exception as e:
        logger.error(f"Error in system health check: {str(e)}")
        return {"success": False, "error": str(e)}


def send_system_alert(health_status: Dict, critical_failures: List[str]):
    """
    Send system alert to administrators
    """
    try:
        # Get admin users
        admin_users = User.objects.filter(
            user_type=UserType.ADMIN.value, is_active=True
        )
        admin_emails = [admin.email for admin in admin_users]

        if not admin_emails:
            logger.warning("No admin users found to send system alerts")
            return

        subject = "🚨 Critical System Alert - Healthcare Management System"

        message = f"""
CRITICAL SYSTEM ALERT

The following critical systems are experiencing issues:
{chr(10).join(f'• {system}' for system in critical_failures)}

Full Health Status:
• Database Connection: {'✅' if health_status['database_connection'] else '❌'}
• Cache Connection: {'✅' if health_status['cache_connection'] else '❌'}
• Email Service: {'✅' if health_status['email_service'] else '❌'}
• Appointment System: {'✅' if health_status['appointment_system'] else '❌'}
• Report System: {'✅' if health_status['report_system'] else '❌'}

Errors:
{chr(10).join(f'• {error}' for error in health_status['errors'])}

Please investigate immediately.

Alert Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S %Z')}
        """

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=admin_emails,
            fail_silently=False,
        )

        logger.warning(f"System alert sent to {len(admin_emails)} administrators")

    except Exception as e:
        logger.error(f"Failed to send system alert: {str(e)}")


def generate_weekly_summary_report():
    """
    Generate weekly summary report for administrators
    Should be run every Monday at 8:00 AM
    """
    try:
        logger.info("Starting weekly summary report generation")

        # Calculate date range for past week
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=7)

        # Gather weekly statistics
        weekly_stats = {
            "period": f"{start_date} to {end_date}",
            "appointments": {},
            "users": {},
            "system": {},
        }

        # Appointment statistics
        week_appointments = Appointment.objects.filter(
            appointment_date__gte=start_date, appointment_date__lte=end_date
        )

        weekly_stats["appointments"] = {
            "total": week_appointments.count(),
            "completed": week_appointments.filter(status=Appointment.COMPLETED).count(),
            "cancelled": week_appointments.filter(status=Appointment.CANCELLED).count(),
            "pending": week_appointments.filter(status=Appointment.PENDING).count(),
        }

        # User statistics
        new_patients = User.objects.filter(
            user_type=UserType.PATIENT.value,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
        ).count()

        new_doctors = User.objects.filter(
            user_type=UserType.DOCTOR.value,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
        ).count()

        weekly_stats["users"] = {
            "new_patients": new_patients,
            "new_doctors": new_doctors,
            "total_active_users": User.objects.filter(is_active=True).count(),
        }

        # System statistics
        weekly_stats["system"] = {
            "total_doctors": User.objects.filter(
                user_type=UserType.DOCTOR.value, is_active=True
            ).count(),
            "total_patients": User.objects.filter(
                user_type=UserType.PATIENT.value, is_active=True
            ).count(),
            "reports_generated": 0,  # Will be filled by report service
        }

        # Send weekly summary to admins
        send_weekly_summary_to_admins(weekly_stats)

        logger.info("Weekly summary report generated successfully")
        return {"success": True, "summary": weekly_stats}

    except Exception as e:
        logger.error(f"Error generating weekly summary report: {str(e)}")
        return {"success": False, "error": str(e)}


def send_weekly_summary_to_admins(weekly_stats: Dict):
    """
    Send weekly summary report to administrators
    """
    try:
        admin_users = User.objects.filter(
            user_type=UserType.ADMIN.value, is_active=True
        )
        admin_emails = [admin.email for admin in admin_users]

        if not admin_emails:
            return

        subject = f"📊 Weekly System Summary - {weekly_stats['period']}"

        message = f"""
Weekly System Summary Report
Period: {weekly_stats['period']}

📅 APPOINTMENTS
• Total Appointments: {weekly_stats['appointments']['total']}
• Completed: {weekly_stats['appointments']['completed']}
• Cancelled: {weekly_stats['appointments']['cancelled']}
• Pending: {weekly_stats['appointments']['pending']}

👥 USER ACTIVITY
• New Patients: {weekly_stats['users']['new_patients']}
• New Doctors: {weekly_stats['users']['new_doctors']}
• Total Active Users: {weekly_stats['users']['total_active_users']}

🏥 SYSTEM STATUS
• Active Doctors: {weekly_stats['system']['total_doctors']}
• Active Patients: {weekly_stats['system']['total_patients']}

This automated report provides insights into your healthcare system's weekly performance.

Best regards,
Healthcare Management System
        """

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=admin_emails,
            fail_silently=False,
        )

        logger.info(f"Weekly summary sent to {len(admin_emails)} administrators")

    except Exception as e:
        logger.error(f"Failed to send weekly summary: {str(e)}")


# Task registry for easy management
SCHEDULED_TASKS = {
    "send_appointment_reminders": {
        "function": send_appointment_reminders,
        "schedule": "Daily at 9:00 AM",
        "description": "Send appointment reminders 24 hours before appointments",
    },
    "generate_monthly_reports": {
        "function": generate_monthly_reports,
        "schedule": "1st of each month at 2:00 AM",
        "description": "Generate monthly reports for all doctors",
    },
    "cleanup_old_data": {
        "function": cleanup_old_data,
        "schedule": "Weekly on Sunday at 3:00 AM",
        "description": "Clean up old data and perform maintenance",
    },
    "system_health_check": {
        "function": system_health_check,
        "schedule": "Every hour",
        "description": "Perform system health checks",
    },
    "generate_weekly_summary_report": {
        "function": generate_weekly_summary_report,
        "schedule": "Weekly on Monday at 8:00 AM",
        "description": "Generate weekly summary for administrators",
    },
}


def run_task(task_name: str) -> Dict[str, Any]:
    """
    Manually run a specific task (useful for testing or manual execution)
    """
    if task_name not in SCHEDULED_TASKS:
        return {"success": False, "error": f"Task {task_name} not found"}

    try:
        task_function = SCHEDULED_TASKS[task_name]["function"]
        result = task_function()
        logger.info(f"Manually executed task {task_name}: {result}")
        return result
    except Exception as e:
        logger.error(f"Error manually running task {task_name}: {str(e)}")
        return {"success": False, "error": str(e)}


def get_task_status() -> Dict[str, Any]:
    """
    Get status information about all scheduled tasks
    """
    return {
        "total_tasks": len(SCHEDULED_TASKS),
        "tasks": {
            name: {"schedule": info["schedule"], "description": info["description"]}
            for name, info in SCHEDULED_TASKS.items()
        },
        "last_check": timezone.now().isoformat(),
    }
