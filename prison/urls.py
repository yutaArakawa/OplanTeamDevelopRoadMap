from django.urls import path
from prison.views import (
    PrisonView
)

urlpatterns = [
    path('top/', PrisonView.as_view(), name='prison'),
]