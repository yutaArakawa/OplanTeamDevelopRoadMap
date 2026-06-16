from django.urls import path
from . import views
from prison.views import (
    PrisonView
)

urlpatterns = [
    path('top/', PrisonView.as_view(), name='prison'),
    path('escape', views.escape, name='prison_escape'),
]
