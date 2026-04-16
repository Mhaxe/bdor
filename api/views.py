from django.core.cache import cache
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.services.player_ranking_service import PlayerRankingService
from api.services.external_stats_service import ExternalStatsService
from api.selectors import delete_fetch_record
from utils.cache import cache_lock

RANKINGS_CACHE_TIMEOUT = 60 * 60 * 12
RANKINGS_CACHE_KEY = "api:rankings:v1"


class Rankings(APIView):
    """API view that returns player points calculations as JSON"""

    def get(self, request):
        response_data = cache.get(RANKINGS_CACHE_KEY)
        if response_data is None:
            with cache_lock(f"lock:{RANKINGS_CACHE_KEY}", timeout=60, wait_timeout=10) as acquired:
                response_data = cache.get(RANKINGS_CACHE_KEY)
                if response_data is None:
                    player_points = PlayerRankingService.get_player_rankings()
                    response_data = self.build_response_data(player_points)
                    cache.set(
                        RANKINGS_CACHE_KEY,
                        response_data,
                        timeout=RANKINGS_CACHE_TIMEOUT,
                    )
        return Response(response_data, status=status.HTTP_200_OK)
    
    def build_response_data(self, player_points):
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

class ClearCache(APIView):
    """API view that forcefully clears the cache."""

    def get(self, request):
        cache.clear()
        return Response({"success": True, "message": "Cache cleared successfully"}, status=status.HTTP_200_OK)

class DeleteFetchRecord(APIView):
    def get(self, request):
        delete_fetch_record()
        return Response({"success": True, "message": "Fetch record deleted successfully"}, status=status.HTTP_200_OK)

class UpdateStats(APIView):
    def get(self, request):
        delete_fetch_record()
        ExternalStatsService.update_stats()
        return Response({"success": True, "message": "Stats updated successfully"}, status=status.HTTP_200_OK)