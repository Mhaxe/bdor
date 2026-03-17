from django.core.cache import cache
from django.utils import timezone
from django.http import HttpResponse
from pathlib import Path
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.services.external_stats_service import ExternalStatsService
from api.services.player_ranking_service import PlayerRankingService


RANKINGS_CACHE_TIMEOUT = 60 * 60 * 24


class Rankings(APIView):
    """API view that returns player points calculations as JSON"""

    def get(self, request):
        try:
            player_points = ExternalStatsService.sync_if_stale()
            cache_key = f"rankings_api_response:{timezone.localdate().isoformat()}"
            cached_response = cache.get(cache_key)
            if cached_response is not None:
                return Response(cached_response, status=status.HTTP_200_OK)

            response_data = {
                "success": True,
                "total_players": len(player_points),
                "players": player_points,
            }
            cache.set(
                cache_key,
                response_data,
                timeout=RANKINGS_CACHE_TIMEOUT,
            )
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            import traceback

            print(f"Error: {e}")
            print(traceback.format_exc())
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ErrorLogs(APIView):
    """API view that returns logged exceptions"""

    def get(self, request):
        """Query AppLog and return the most recent entries."""
        try:
            from api.models import AppLog

            logs = AppLog.objects.all()[:200]
            if not logs:
                return HttpResponse(
                    "No errors logged yet.",
                    content_type="text/plain",
                    status=200,
                )

            lines = []
            for log in logs:
                timestamp = log.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                lines.append(
                    f"[{timestamp}] {log.level} {log.logger_name}: {log.message}\n"
                )
                if log.path or log.method:
                    lines.append(f"    {log.method} {log.path}\n")
                if log.exception_type:
                    lines.append(f"    Exception: {log.exception_type}\n")
                if log.traceback:
                    lines.append(f"    Traceback:\n{log.traceback}\n")

            return HttpResponse(
                "\n".join(lines),
                content_type="text/plain",
                status=200,
            )
        except Exception as e:
            import traceback

            return HttpResponse(
                f"Error reading logs: {str(e)}\n\n{traceback.format_exc()}",
                content_type="text/plain",
                status=500,
            )
