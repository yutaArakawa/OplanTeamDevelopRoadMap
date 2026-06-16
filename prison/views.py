from django.views.generic import TemplateView

# Create your views here.


class PrisonView(TemplateView):
    template_name = 'prison/prison_top.html'

