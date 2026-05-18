from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
#from django.contrib.auth.decorators import login_required

# Create your views here.

#@login_required
#def home(request):
#    return render(request, 'dashboard/home.html')

from django.views.generic import TemplateView
from common.mixins import AdminRequiredMixin

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/home.html'