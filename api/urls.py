from django.urls import path

from .views import Rankings, FAQs, ClearCache, DeleteFetchRecord

urlpatterns = [
    path("rankings/", Rankings.as_view()),
    path("faqs/", FAQs.as_view()),
    path("clear-cache/", ClearCache.as_view(), name="clear-cache"),
    path("delete-fetch-record/", DeleteFetchRecord.as_view(), name="delete-fetch-record"),
]
