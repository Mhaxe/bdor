from django.urls import path

from .views import Rankings, FAQs, ExternalStats

urlpatterns = [
    path("rankings/", Rankings.as_view()),
    path("faqs/", FAQs.as_view()),
    path("external-stats/", ExternalStats.as_view(), name="external-stats"),
]
