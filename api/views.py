from django.core.cache import cache
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.services.player_ranking_service import PlayerRankingService
from api.services.external_stats_service import ExternalStatsService
from api.selectors import delete_fetch_record

RANKINGS_CACHE_TIMEOUT = 60 * 60 * 12
RANKINGS_CACHE_KEY = "api:rankings:v1"


class Rankings(APIView):
    """API view that returns player points calculations as JSON"""

    def get(self, request):
        try:
            response_data = cache.get(RANKINGS_CACHE_KEY)
            if response_data is None:
                if ExternalStatsService.should_fetch_today():
                    try:
                        response_data = ExternalStatsService.update_stats()
                    except Exception as e:
                        response_data = self.get_local_rankings()
                else:
                    response_data = self.get_local_rankings()
                cache.set(
                    RANKINGS_CACHE_KEY,
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
    
    def get_local_rankings(self):
        player_points = PlayerRankingService.get_player_rankings()
        return {
            "success": True,
            "total_players": len(player_points),
            "players": player_points,
        }


class FAQs(APIView):
    def get(self, request):
        from api.serializers import FAQPointsSystemSerializer

        serializer = FAQPointsSystemSerializer(instance={})
        return Response(serializer.data, status=status.HTTP_200_OK)


class ExternalStats(APIView):
    """API view that triggers external stats synchronization and returns the current rankings."""

    def get(self, request):
        try:
            # Using sync_if_stale to trigger a fetch only if today's data is missing.
            player_points = ExternalStatsService.sync_if_stale()
            response_data = {
                "success": True,
                "total_players": len(player_points),
                "players": player_points,
            }
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            import traceback
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in ExternalStats view: {e}")
            logger.error(traceback.format_exc())
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ClearCache(APIView):
    """API view that forcefully clears the cache."""

    def get(self, request):
        cache.clear()
        return Response({"success": True, "message": "Cache cleared successfully"}, status=status.HTTP_200_OK)

class DeleteFetchRecord(APIView):
    def get(self, request):
        delete_fetch_record()
        return Response({"success": True, "message": "Fetch record deleted successfully"}, status=status.HTTP_200_OK)
