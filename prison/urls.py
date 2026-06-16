from django.urls import path
from . import views

urlpatterns = [
    path('escape', views.escape, name='prison_escape'),
]
