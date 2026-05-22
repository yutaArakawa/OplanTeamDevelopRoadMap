from django.urls import path
from .views import (
    InquiryListView,
    InquiryCreateView,
    InquiryGuestCreateView,
    InquiryDetailView,
    InquiryDeleteView,
)

urlpatterns = [
    path('', InquiryListView.as_view(), name='inquiry_list'),
    path('create/', InquiryCreateView.as_view(), name='inquiry_create'),
    path('create/guest/', InquiryGuestCreateView.as_view(), name='inquiry_create_guest'),
    path('<int:pk>/', InquiryDetailView.as_view(), name='inquiry_detail'),
    path('<int:pk>/delete/', InquiryDeleteView.as_view(), name='inquiry_delete'),
]
