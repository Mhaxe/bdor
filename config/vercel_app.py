import os
import sys

# Ensure the project base dir is on sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from balon_dor.wsgi import application  # noqa: E402


# Vercel's python runtime looks for a `handler` name for WSGI/ASGI apps.
# Expose the WSGI application as `handler`.
def handler(environ, start_response):
    return application(environ, start_response)
