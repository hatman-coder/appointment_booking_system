from django.db import connection
from rich.console import Console

console = Console()


class SQLLoggingMiddleware:
    """
    Middleware to log and prettify SQL queries for every HTTP request,
    with optional filtering by path or request type.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip logging for certain paths
        if self.should_skip_logging(request):
            return self.get_response(request)

        # Process the request and generate the response
        response = self.get_response(request)

        # Log SQL queries after generating the response
        self.log_prettified_sql()

        return response

    def should_skip_logging(self, request):
        """
        Determine if the request should skip SQL logging.
        """
        # Example: Skip static files, admin paths, and health-check URLs
        excluded_paths = ["/static/", "/admin/", "/health/"]
        return any(request.path.startswith(path) for path in excluded_paths)

    def log_prettified_sql(self):
        """Log SQL queries executed during the request."""
        if connection.queries:
            console.print("\n[bold cyan]RAW SQL Queries:[/bold cyan]\n")
            for query in connection.queries:
                sql = query.get("sql", "N/A")
                time = query.get("time", "N/A")
                console.print(f"[bold yellow]Time:[/bold yellow] {time}s")
                console.print(f"[bold green]SQL:[/bold green] {sql}\n")
