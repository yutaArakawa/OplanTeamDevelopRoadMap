from datetime import timedelta
from django.urls import path
from dashboard import api_views

urlpatterns = [
    path('', api_views.HomeAPIView.as_view(), name='api_dashboard'),
]