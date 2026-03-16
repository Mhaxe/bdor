from django.urls import path

from .views import Rankings

urlpatterns = [
    path("rankings/", Rankings.as_view(), name="player-points"),
]
