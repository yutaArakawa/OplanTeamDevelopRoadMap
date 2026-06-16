from django.shortcuts import render
from django.views.generic import TemplateView

class PrisonView(TemplateView):
    template_name = 'prison/prison_top.html'

def escape(request):
    return render(request, 'prison/escape.html')
