from django.urls import path

from .views import ClearCache, FAQs, Rankings

urlpatterns = [
    path("rankings/", Rankings.as_view()),
    path("faqs/", FAQs.as_view()),
    path("cc/", ClearCache.as_view(), name="clear-cache"),
]
