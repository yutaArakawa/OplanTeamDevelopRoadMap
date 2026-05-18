from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from .views import UserListView, UserCreateView

urlpatterns = [
    path(
        'login/',
        LoginView.as_view(
            template_name='accounts/login.html'
        ),
        name='login'
    ),

    path(
        'logout/',
        LogoutView.as_view(),
        name='logout'
    ),

    path(
        'user_list/',
        UserListView.as_view(),
        name='user_list'
    ),

    path(
        'user_create/',
        UserCreateView.as_view(),
        name='user_create'
    ),

]