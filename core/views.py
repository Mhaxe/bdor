from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView


class IndexView(View):
    def get(self, request):
        return redirect("rankings")

class RankingView(TemplateView):
    template_name = "index.html"