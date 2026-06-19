from django.urls import path
from accounts import api_accounts_views

urlpatterns = [
    path('user/list/', api_accounts_views.UserListAPIView.as_view(), name='api_user_list'),
]