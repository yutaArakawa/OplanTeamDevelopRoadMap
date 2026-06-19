from django.urls import path
from accounts import api_auth_views

urlpatterns = [
    path('me/', api_auth_views.MeAPIView.as_view(), name='api_me'),
    path('csrf/', api_auth_views.CsrfAPIView.as_view(), name='api_csrf'),
    path('login/', api_auth_views.LoginAPIView.as_view(), name='api_login'),
    path('logout/', api_auth_views.LogoutAPIView.as_view(), name='api_logout'),
]