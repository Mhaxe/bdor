import time
import logging
from typing import Tuple

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse

logger = logging.getLogger(__name__)


def _parse_rate(rate: str) -> Tuple[int, int]:
    """Parse rate strings like '600/min' -> (600, 60)."""
    try:
        count, per = rate.split("/")
        count = int(count)
        if per == "min":
            window = 60
        elif per == "hour":
            window = 3600
        elif per == "day":
            window = 86400
        else:
            window = int(per)
        return count, window
    except Exception:
        # Fallback to conservative default
        return 60, 60


def _get_client_ip(request) -> str:
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        # first IP is the client
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


class RateLimitMiddleware:
    """Simple fixed-window rate limiting middleware using Django cache.

    Notes:
    - Uses settings.RATE_LIMIT_* configuration
    - Exempts paths in settings.RATE_LIMIT_WHITELIST and static files (/static/)
    """

    def __init__(self, get_response):
        self.get_response = get_response

        self.anon_count, self.anon_window = _parse_rate(
            getattr(settings, "RATE_LIMIT_ANON", "60/min")
        )
        self.user_count, self.user_window = _parse_rate(
            getattr(settings, "RATE_LIMIT_USER", "600/min")
        )
        self.prefix = getattr(settings, "RATE_LIMIT_CACHE_PREFIX", "rl:")
        self.whitelist = getattr(settings, "RATE_LIMIT_WHITELIST", [])

    def __call__(self, request):
        # Skip static files and admin media
        path = request.path
        if path.startswith(getattr(settings, "STATIC_URL", "/static/")):
            return self.get_response(request)

        # Whitelist by path or IP
        client_ip = _get_client_ip(request)
        for w in self.whitelist:
            if not w:
                continue
            if w == client_ip or path.startswith(w):
                return self.get_response(request)

        if getattr(request, "user", None) and request.user.is_authenticated:
            identifier = f"user:{request.user.id}"
            count = self.user_count
            window = self.user_window
        else:
            identifier = f"ip:{client_ip}"
            count = self.anon_count
            window = self.anon_window

        # Fixed-window key: prefix:identifier:window_start
        window_start = int(time.time() // window)
        key = f"{self.prefix}{identifier}:{window_start}"

        try:
            current = cache.incr(key)
        except Exception:
            # If key does not exist or backend doesn't support incr, try to add
            try:
                cache.add(key, 1, timeout=window)
                current = 1
            except Exception:
                # As a last resort, allow the request but log
                logger.exception("Rate limit cache operation failed; allowing request")
                return self.get_response(request)
        else:
            # If this was the first increment (i.e., key was created by incr), ensure TTL
            if current == 1:
                try:
                    cache.expire(key, window)
                except Exception:
                    # expire may not exist on some backends; ignore
                    pass

        remaining = max(0, count - int(current))
        # Attach headers on response
        response = None
        if int(current) > count:
            retry_after = (window * (window_start + 1)) - int(time.time())
            response = HttpResponse(
                "Too Many Requests",
                status=429,
            )
            response["Retry-After"] = str(retry_after)
            response["X-RateLimit-Limit"] = str(count)
            response["X-RateLimit-Remaining"] = "0"
            logger.info(
                "Rate limit exceeded: %s path=%s ip=%s", identifier, path, client_ip
            )
            return response

        # Proceed and add headers to the eventual response
        response = self.get_response(request)
        response["X-RateLimit-Limit"] = str(count)
        response["X-RateLimit-Remaining"] = str(remaining)
        return response
