import os
import datetime
import logging
from config import settings

logger = logging.getLogger(__name__)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Set up logging configuration
        log_dir = 'logs'
        log_file = 'requests.log'
        log_file_path = os.path.join(log_dir, log_file)

        # Ensure the logs directory exists
        os.makedirs(log_dir, exist_ok=True)

        # Check if the log file exists, if not, create it
        if not os.path.exists(log_file_path):
            with open(log_file_path, 'w'):
                pass

        logging.basicConfig(filename=log_file_path, level=logging.INFO,
                            format='%(levelname)s - %(message)s')

        # try:
        #     os.chmod(log_file_path, 0o644)
        # except OSError:
        #     print(f"Failed to set file permissions for {log_file_path}")

    def __call__(self, request):
        # Log the IP address and the request
        ip = get_client_ip(request)
        response = self.get_response(request)
        status_code = response.status_code
        logger.info(
            f"{datetime.datetime.now().strftime('%Y-%m-%d -- %I:%M %p')} -- Request from {ip} -- "
            f"{request.method} -- {status_code} {request.path}")
        return response


