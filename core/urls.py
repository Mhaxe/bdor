from django.urls import path

from .views import IndexView, RankingView, FAQsView

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("rankings/", RankingView.as_view(), name="rankings"),
    path("faqs/", FAQsView.as_view(), name="faqs"),
]
