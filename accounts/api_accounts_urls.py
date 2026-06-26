from django.urls import path
from accounts import api_accounts_views

urlpatterns = [
    path('user/list/', api_accounts_views.UserListAPIView.as_view(), name='api_user_list'),
    path('user/create/', api_accounts_views.UserCreateAPIView.as_view(), name='api_user_create'),
    path('user/<int:pk>/', api_accounts_views.UserDetailAPIView.as_view(), name='api_user_detail'),
]
