import traceback
from datetime import datetime
import time
from django.utils.deprecation import MiddlewareMixin


class ExceptionLoggingMiddleware:
    """
    Middleware that catches unhandled exceptions and logs them to the database.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            self._log_exception(e, request)
            raise

    def _log_exception(self, exception, request):
        """Log exception details to database"""
        try:
            from api.models import AppLog
            AppLog.objects.create(
                level='ERROR',
                logger_name='api.middleware.ExceptionLoggingMiddleware',
                message=str(exception),
                path=request.path,
                method=request.method,
                exception_type=type(exception).__name__,
                traceback=traceback.format_exc(),
            )
        except Exception:
            pass  # Silently fail to avoid recursive errors