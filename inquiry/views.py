from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.views import View
from django.views.generic import TemplateView
from django.urls import reverse_lazy

from inquiry.models import Inquiry
from inquiry.forms import InquiryCreateForm, InquiryGuestCreateForm, InquiryStatusUpdateForm
from accounts.models import Authority
from inventory.models import Shop, Warehouse
from common.constants import AUTHORITY_ADMIN, AUTHORITY_SHOP, AUTHORITY_WAREHOUSE


# ---------------------------------------------------------------------------
# Mixin
# ---------------------------------------------------------------------------

class NonAdminRequiredMixin(LoginRequiredMixin):
    """ログイン済み かつ 管理者以外 のみ通す Mixin"""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.authority_id == AUTHORITY_ADMIN:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------

def _is_receiver(user, inquiry):
    """ログインユーザーが inquiry の受信者かどうかを返す"""
    if user.authority_id != inquiry.to_authority_id:
        return False
    if user.authority_id == AUTHORITY_SHOP:
        return inquiry.to_relation is not None and inquiry.to_relation.shop == user.shop
    if user.authority_id == AUTHORITY_WAREHOUSE:
        return inquiry.to_relation is not None and inquiry.to_relation.warehouse == user.warehouse
    # 管理者: 権限が一致すれば受信者
    return True


# ---------------------------------------------------------------------------
# 問い合わせ一覧
# ---------------------------------------------------------------------------

class InquiryListView(LoginRequiredMixin, TemplateView):
    template_name = 'inquiry/inquiry_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # ---- 受信一覧 ----
        received = Inquiry.active_objects.filter(
            to_authority_id=user.authority_id
        )
        if user.authority_id == AUTHORITY_SHOP:
            received = received.filter(to_relation__shop=user.shop)
        elif user.authority_id == AUTHORITY_WAREHOUSE:
            received = received.filter(to_relation__warehouse=user.warehouse)

        # ---- 送信済み一覧 ----
        sent = Inquiry.active_objects.filter(from_user=user)

        # ---- 絞り込み (受信側) ----
        sort_authority = self.request.GET.get('authority')
        if sort_authority:
            try:
                received = received.filter(from_authority_id=int(sort_authority))
            except ValueError:
                pass

        sort_shop = self.request.GET.get('shop')
        if sort_shop:
            try:
                received = received.filter(from_belong_shop_id=int(sort_shop))
            except ValueError:
                pass

        sort_warehouse = self.request.GET.get('warehouse')
        if sort_warehouse:
            try:
                received = received.filter(from_belong_warehouse_id=int(sort_warehouse))
            except ValueError:
                pass

        # ---- ステータス絞り込み (両方) ----
        sort_status = self.request.GET.get('status')
        if sort_status is not None and sort_status != '':
            try:
                status_val = int(sort_status)
                received = received.filter(status=status_val)
                sent = sent.filter(status=status_val)
            except ValueError:
                pass

        context['received_inquiries'] = received.order_by('-created_at')
        context['sent_inquiries'] = sent.order_by('-created_at')

        # 絞り込みUI用マスタ
        context['authorities'] = Authority.objects.all()
        context['shops'] = Shop.active_objects.all()
        context['warehouses'] = Warehouse.active_objects.all()
        context['status_choices'] = Inquiry.Status.choices

        return context


# ---------------------------------------------------------------------------
# 問い合わせ送信（ログイン済み・管理者以外）
# ---------------------------------------------------------------------------

class InquiryCreateView(NonAdminRequiredMixin, View):
    template_name = 'inquiry/inquiry_create.html'
    success_url = reverse_lazy('inquiry_list')

    def get(self, request, *args, **kwargs):
        relation_id = request.GET.get('relation')
        form = InquiryCreateForm(login_user=request.user, relation_id=relation_id)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = InquiryCreateForm(request.POST, login_user=request.user)
        if form.is_valid():
            form.save()
            return redirect(self.success_url)
        return render(request, self.template_name, {'form': form})


# ---------------------------------------------------------------------------
# 問い合わせ送信（未ログインゲスト）
# ---------------------------------------------------------------------------

class InquiryGuestCreateView(View):
    template_name = 'inquiry/inquiry_create_guest.html'

    def get(self, request, *args, **kwargs):
        form = InquiryGuestCreateForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = InquiryGuestCreateForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
        return render(request, self.template_name, {'form': form})


# ---------------------------------------------------------------------------
# 問い合わせ詳細・ステータス更新
# ---------------------------------------------------------------------------

class InquiryDetailView(LoginRequiredMixin, View):
    template_name = 'inquiry/inquiry_detail.html'

    def _get_inquiry_or_403(self, request, pk):
        inquiry = get_object_or_404(Inquiry.active_objects, pk=pk)
        user = request.user
        is_recv = _is_receiver(user, inquiry)
        is_sender = (inquiry.from_user == user)
        if not is_recv and not is_sender:
            raise PermissionDenied
        return inquiry, is_recv

    def get(self, request, pk, *args, **kwargs):
        inquiry, is_recv = self._get_inquiry_or_403(request, pk)
        form = InquiryStatusUpdateForm(instance=inquiry) if is_recv else None
        return render(request, self.template_name, {
            'inquiry': inquiry,
            'is_receiver': is_recv,
            'form': form,
        })

    def post(self, request, pk, *args, **kwargs):
        inquiry, is_recv = self._get_inquiry_or_403(request, pk)
        if not is_recv:
            raise PermissionDenied
        form = InquiryStatusUpdateForm(request.POST, instance=inquiry)
        if form.is_valid():
            form.save()
            return redirect('inquiry_detail', pk=pk)
        return render(request, self.template_name, {
            'inquiry': inquiry,
            'is_receiver': is_recv,
            'form': form,
        })


# ---------------------------------------------------------------------------
# 問い合わせ論理削除
# ---------------------------------------------------------------------------

class InquiryDeleteView(LoginRequiredMixin, View):

    def post(self, request, pk, *args, **kwargs):
        inquiry = get_object_or_404(Inquiry.active_objects, pk=pk)
        inquiry.delete_flg = True
        inquiry.save()
        return redirect('inquiry_list')
