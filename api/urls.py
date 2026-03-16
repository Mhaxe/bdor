from django.urls import path

from .views import Rankings, ErrorLogs

urlpatterns = [
    path("rankings/", Rankings.as_view()),
    path("error/", ErrorLogs.as_view()),
]
