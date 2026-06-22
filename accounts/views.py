from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from urllib.parse import urlencode
from accounts.models import User, Authority
from inventory.models import Shop, Warehouse
from common.constants import (AUTHORITY_ADMIN, AUTHORITY_SHOP, AUTHORITY_WAREHOUSE)
from common.mixins import AdminRequiredMixin
from .forms import LoginForm, UserCreateForm, UserUpdateForm , MyPageForm

# Create your views here.

class UserLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = LoginForm

class UserListView(LoginRequiredMixin, ListView):
    template_name = 'accounts/user_list.html'
    model = User
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        if self.request.user.authority_id == AUTHORITY_ADMIN:
            qs = User.active_objects.all()
        else:
            qs = User.active_objects.filter(authority_id=self.request.user.authority_id)

        # 絞り込み - 権限
        sort_authority = self.request.GET.get('authority')
        if sort_authority:
            try:
                qs = qs.filter(authority_id=int(sort_authority))
            except ValueError:
                pass

        # 絞り込み - 所属店舗
        sort_shop = self.request.GET.get('shop')
        if sort_shop:
            try:
                qs = qs.filter(shop_id=int(sort_shop))
            except ValueError:
                pass

        # 絞り込み - 所属倉庫
        sort_warehouse = self.request.GET.get('warehouse')
        if sort_warehouse:
            try:
                qs = qs.filter(warehouse_id=int(sort_warehouse))
            except ValueError:
                pass

        return qs.order_by('id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 絞り込み機能用
        context['authorities'] = Authority.objects.all()
        context['shops'] = Shop.objects.all()
        context['warehouses'] = Warehouse.objects.all()

        # ページネーションリンクに絞り込みパラメータを引き継ぐ
        filter_params = {
            k: self.request.GET[k]
            for k in ('authority', 'shop', 'warehouse')
            if self.request.GET.get(k)
        }
        context['filter_query'] = ('&' + urlencode(filter_params)) if filter_params else ''

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
    
class UserUpdateView(AdminRequiredMixin, UpdateView):
    template_name = 'accounts/user_update.html'
    model = User
    form_class = UserUpdateForm
    success_url = reverse_lazy('user_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_authority_id'] = self.request.user.authority_id
        context['AUTHORITY_ADMIN'] = AUTHORITY_ADMIN
        context['AUTHORITY_SHOP'] = AUTHORITY_SHOP
        context['AUTHORITY_WAREHOUSE'] = AUTHORITY_WAREHOUSE
        return context


class MyPageView(LoginRequiredMixin, UpdateView):
    template_name = 'accounts/mypage.html'
    model = User
    form_class = MyPageForm
    success_url = reverse_lazy('mypage')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        form.save()
        if form.cleaned_data.get('new_password1'):
            return redirect('login')
        messages.success(self.request, 'プロフィールを更新しました。')
        return redirect('mypage')


class UserDeleteView(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        user = get_object_or_404(
            User,
            pk=kwargs['pk']
        )

        if user == request.user:
            return redirect('user_update', pk=user.pk)
        user.delete_flg = True
        user.save()
        
        return redirect('user_list')

    
