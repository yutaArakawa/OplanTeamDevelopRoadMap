from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from .views import UserLoginView, UserListView, UserCreateView, UserDeleteView, MyPageView

urlpatterns = [
    path(
        'login/',
        UserLoginView.as_view(
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
        'mypage/',
        MyPageView.as_view(),
        name='mypage'
    ),

    path(
        'user/list/',
        UserListView.as_view(),
        name='user_list'
    ),

    path(
        'user/create/',
        UserCreateView.as_view(),
        name='user_create'
    ),

    path(
        'user/delete/<int:pk>/',
        UserDeleteView.as_view(),
        name='user_delete'
    ),

]