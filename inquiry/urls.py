from django.urls import path
from .views import (
    InquiryListView,
    InquiryCreateView,
    InquiryGuestCreateView,
    InquiryDetailView,
    InquiryDeleteView,
    InquiryCategoryListView,
    InquiryCategoryCreateView,
    InquiryCategoryUpdateView,
    InquiryCategoryDeleteView,
)

urlpatterns = [
    path('', InquiryListView.as_view(), name='inquiry_list'),
    path('create/', InquiryCreateView.as_view(), name='inquiry_create'),
    path('create/guest/', InquiryGuestCreateView.as_view(), name='inquiry_create_guest'),
    path('<int:pk>/', InquiryDetailView.as_view(), name='inquiry_detail'),
    path('<int:pk>/delete/', InquiryDeleteView.as_view(), name='inquiry_delete'),
    path('categories/', InquiryCategoryListView.as_view(), name='inquiry_category_list'),
    path('categories/create/', InquiryCategoryCreateView.as_view(), name='inquiry_category_create'),
    path('categories/<int:pk>/edit/', InquiryCategoryUpdateView.as_view(), name='inquiry_category_edit'),
    path('categories/<int:pk>/delete/', InquiryCategoryDeleteView.as_view(), name='inquiry_category_delete'),
]
