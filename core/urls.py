from django.urls import path

from .views import IndexView, RankingView

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("rankings/", RankingView.as_view(), name="rankings"),
]
