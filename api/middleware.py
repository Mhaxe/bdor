import traceback
import os
from datetime import datetime
from pathlib import Path


class ExceptionLoggingMiddleware:
    """
    Middleware that catches unhandled exceptions and logs them to a file.
    Logs are stored in logs/exceptions.log
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Create logs directory if it doesn't exist
        self.log_dir = Path(__file__).resolve().parent.parent / "logs"
        self.log_dir.mkdir(exist_ok=True)
        self.log_file = self.log_dir / "exceptions.log"
    
    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            # Log the exception
            self._log_exception(e, request)
            # Re-raise to let Django handle it
            raise
    
    def _log_exception(self, exception, request):
        """Log exception details to file"""
        try:
            timestamp = datetime.now().isoformat()
            tb = traceback.format_exc()
            
            # Format the log message
            log_message = f"""
{'='*80}
Timestamp: {timestamp}
Method: {request.method}
Path: {request.path}
Exception Type: {type(exception).__name__}
Exception: {str(exception)}
Traceback:
{tb}
{'='*80}
"""
            
            # Append to log file
            with open(self.log_file, "a") as f:
                f.write(log_message)
        except Exception as log_error:
            # Silently fail if logging fails to avoid recursive errors
            pass
