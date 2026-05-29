from django.urls import path
from .views import UserLoginView, UserLogoutView, UserListView, UserCreateView, UserUpdateView, UserDeleteView

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
        UserLogoutView.as_view(),
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

    path(
        'user_update/<int:pk>/',
        UserUpdateView.as_view(),
        name='user_update'
    ),

    path(
        'user_delete/<int:pk>/',
        UserDeleteView.as_view(),
        name='user_delete'
    ),

]