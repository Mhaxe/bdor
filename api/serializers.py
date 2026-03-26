from rest_framework import serializers

from core.points_system import (
    DefenderPointsSystem,
    KeeperPointsSystem,
    MidfielderPointsSystem,
    StrikerPointsSystem,
)


class FAQPointsSystemSerializer(serializers.Serializer):
    """
    Serializer to expose the points system configuration for the FAQs view.
    """

    points_system = serializers.SerializerMethodField()

    def get_points_system(self, obj):
        return {
            "forward": StrikerPointsSystem.getPointsContext(),
            "midfielder": MidfielderPointsSystem.getPointsContext(),
            "defender": DefenderPointsSystem.getPointsContext(),
            "goalkeeper": KeeperPointsSystem.getPointsContext(),
        }
