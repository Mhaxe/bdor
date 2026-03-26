from django.urls import path

from .views import Rankings, ErrorLogs, FAQs

urlpatterns = [
    path("rankings/", Rankings.as_view()),
    path("faqs/", FAQs.as_view()),
    path("error/", ErrorLogs.as_view()),
]
