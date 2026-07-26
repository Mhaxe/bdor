import secrets

from django.conf import settings
from django.core.cache import cache
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.services.s3_summary_service import S3SummaryService, SummaryNotAvailable
from utils.cache import cache_lock

RANKINGS_CACHE_TIMEOUT = 60 * 60 * 12
RANKINGS_CACHE_KEY = "api:rankings:v1"


class Rankings(APIView):
    """API view that returns player points calculations as JSON"""

    def get(self, request):
        response_data = cache.get(RANKINGS_CACHE_KEY)
        if response_data is None:
            with cache_lock(f"lock:{RANKINGS_CACHE_KEY}", timeout=60, wait_timeout=10):
                response_data = cache.get(RANKINGS_CACHE_KEY)
                if response_data is None:
                    try:
                        response_data = self.load_response_data()
                    except SummaryNotAvailable:
                        return Response(
                            {
                                "success": False,
                                "status": "not_ready",
                                "message": "Rankings data is not available yet. Please check back shortly.",
                                "total_players": 0,
                                "players": [],
                            },
                            status=status.HTTP_503_SERVICE_UNAVAILABLE,
                        )
                    cache.set(
                        RANKINGS_CACHE_KEY,
                        response_data,
                        timeout=RANKINGS_CACHE_TIMEOUT,
                    )
        return Response(response_data, status=status.HTTP_200_OK)

    def load_response_data(self):
        summary = S3SummaryService.get_latest_summary()
        return self.build_response_data(summary["players"])

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
    """Admin-only API view that forcefully clears the rankings cache entry."""

    def get(self, request):
        provided = request.headers.get("X-Admin-Token", "")
        if not settings.ADMIN_API_TOKEN or not secrets.compare_digest(provided, settings.ADMIN_API_TOKEN):
            return Response({"success": False, "message": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        cache.delete(RANKINGS_CACHE_KEY)
        return Response({"success": True, "message": "Cache cleared successfully"}, status=status.HTTP_200_OK)
