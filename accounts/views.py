from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, CreateView
from django.urls import reverse_lazy
from accounts.models import User, Authority
from inventory.models import Shop, Warehouse
from common.constants import (AUTHORITY_ADMIN, AUTHORITY_SHOP, AUTHORITY_WAREHOUSE)
from .forms import UserCreateForm

# Create your views here.

class UserListView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/user_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.authority_id == AUTHORITY_ADMIN:
            users = User.objects.all()
        else:
            users = User.objects.filter(authority_id=self.request.user.authority_id)

        # 絞り込み - 権限
        sort_authority = self.request.GET.get('authority')
        if sort_authority:
            users = users.filter(
                authority_id=sort_authority
            )
        # 絞り込み - 所属
        sort_shop = self.request.GET.get('shop')
        if sort_shop:
            users = users.filter(
                shop_id=sort_shop
            )
        sort_warehouse = self.request.GET.get('warehouse')
        if sort_warehouse:
            users = users.filter(
                warehouse_id=sort_warehouse
            )

        context['users'] = users

        # 絞り込み機能用
        # 権限一覧
        authorities = Authority.objects.all()
        context['authorities'] = authorities
        # 店舗一覧
        shops = Shop.objects.all()
        context['shops'] = shops
        # 倉庫一覧
        warehouses = Warehouse.objects.all()
        context['warehouses'] = warehouses

        return context

class UserCreateView(LoginRequiredMixin, CreateView):
    template_name = 'accounts/user_create.html'
    model = User
    form_class = UserCreateForm
    success_url = reverse_lazy('user_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
