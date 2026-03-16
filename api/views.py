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
            ExternalStatsService.sync_if_stale()
            cache_key = f"rankings_api_response:{timezone.localdate().isoformat()}"
            cached_response = cache.get(cache_key)
            if cached_response is not None:
                return Response(cached_response, status=status.HTTP_200_OK)

            player_points = PlayerRankingService.get_player_rankings()
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
        """Get the exceptions log file content"""
        try:
            log_file = Path(__file__).resolve().parent.parent / "logs" / "exceptions.log"
            
            if not log_file.exists():
                return HttpResponse(
                    "No errors logged yet.",
                    content_type="text/plain",
                    status=200
                )
            
            with open(log_file, "r") as f:
                content = f.read()
            
            return HttpResponse(content, content_type="text/plain", status=200)
        except Exception as e:
            import traceback
            return HttpResponse(
                f"Error reading logs: {str(e)}\n\n{traceback.format_exc()}",
                content_type="text/plain",
                status=500
            )
