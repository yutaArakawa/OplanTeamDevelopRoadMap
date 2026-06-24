from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from common.exceptions import ForbiddenException, NotFoundException
from django.views import View
from django.views.generic import TemplateView, CreateView, UpdateView
from django.urls import reverse_lazy, reverse

from inquiry.models import Inquiry, InquiryCategory
from inquiry.forms import InquiryCreateForm, InquiryGuestCreateForm, InquiryStatusUpdateForm, InquiryCategoryForm
from accounts.models import Authority
from inventory.models import Shop, Warehouse
from common.constants import AUTHORITY_ADMIN, AUTHORITY_SHOP, AUTHORITY_WAREHOUSE
from common.mixins import AdminRequiredMixin, ShopStaffRequiredMixin, WarehouseStaffRequiredMixin
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit, urlparse


# ---------------------------------------------------------------------------
# Mixin
# ---------------------------------------------------------------------------

class NonAdminRequiredMixin(LoginRequiredMixin):
    """ログイン済み かつ 管理者以外 のみ通す Mixin"""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.authority_id == AUTHORITY_ADMIN:
            raise ForbiddenException
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
        ).select_related(
            'inquiry_category',
        )
        if user.authority_id == AUTHORITY_SHOP:
            received = received.filter(to_relation__shop=user.shop)
        elif user.authority_id == AUTHORITY_WAREHOUSE:
            received = received.filter(to_relation__warehouse=user.warehouse)

        # ---- 送信済み一覧 ----
        sent = Inquiry.active_objects.filter(from_user=user).select_related(
            'to_relation',
            'to_relation__shop',
            'to_relation__warehouse',
            'inquiry_category',
            )

        # ---- 絞り込み (受信側) ----
        sort_category = self.request.GET.get('category')
        if sort_category:
            try:
                received = received.filter(inquiry_category_id=int(sort_category))
            except ValueError:
                pass

        sort_authority = self.request.GET.get('authority')
        if sort_authority:
            if sort_authority == 'guest':
                received = received.filter(
                    from_user__isnull=True,
                    from_authority__isnull=True,
                )
            else:
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

        sort_status = self.request.GET.get('status')
        if sort_status is not None and sort_status != '':
            try:
                status_val = int(sort_status)
                received = received.filter(status=status_val)
            except ValueError:
                pass

        # ---- 絞り込み (送信側) ----
        sort_sender_category = self.request.GET.get('sender_category')
        if sort_sender_category:
            try:
                sent = sent.filter(inquiry_category_id=int(sort_sender_category))
            except ValueError:
                pass

        sort_sender_to_authority = self.request.GET.get('sender_to_authority')
        if sort_sender_to_authority:
            try:
                sent = sent.filter(to_authority_id=int(sort_sender_to_authority))
            except ValueError:
                pass

        sort_sender_to_shop = self.request.GET.get('sender_to_shop')
        if sort_sender_to_shop:
            try:
                sent = sent.filter(to_relation__shop_id=int(sort_sender_to_shop))
            except ValueError:
                pass

        sort_sender_to_warehouse = self.request.GET.get('sender_to_warehouse')
        if sort_sender_to_warehouse:
            try:
                sent = sent.filter(to_relation__warehouse_id=int(sort_sender_to_warehouse))
            except ValueError:
                pass

        sort_sender_status = self.request.GET.get('sender_status')
        if sort_sender_status is not None and sort_sender_status != '':
            try:
                sender_status_val = int(sort_sender_status)
                sent = sent.filter(status=sender_status_val)
            except ValueError:
                pass

        context['received_inquiries'] = received.order_by('-created_at')
        context['sent_inquiries'] = sent.order_by('-created_at')

        # 絞り込みUI用マスタ
        # 宛先権限: 自分と異なる権限のみ選択可能
        context['categories'] = InquiryCategory.active_objects.all()
        context['authorities'] = Authority.objects.exclude(
            id=user.authority_id
        )
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
            messages.success(self.request, '問い合わせを送信しました。')
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
            messages.success(self.request, '問い合わせを送信しました。')
            return redirect('inquiry_create_guest')
        return render(request, self.template_name, {'form': form})


# ---------------------------------------------------------------------------
# 問い合わせ詳細・ステータス更新
# ---------------------------------------------------------------------------

class InquiryDetailView(LoginRequiredMixin, View):
    template_name = 'inquiry/inquiry_detail.html'

    def _get_inquiry_or_403(self, request, pk):
        inquiry = get_object_or_404(
            Inquiry.active_objects.select_related(
                'to_relation__warehouse',
                'to_relation__shop',
                'inquiry_category',
            ),
            pk=pk
        )
        user = request.user
        is_recv = _is_receiver(user, inquiry)
        is_sender = (inquiry.from_user == user)
        if not is_recv and not is_sender:
            raise ForbiddenException
        return inquiry, is_recv

    def get(self, request, pk, *args, **kwargs):
        inquiry, is_recv = self._get_inquiry_or_403(request, pk)
        form = InquiryStatusUpdateForm(instance=inquiry) if is_recv else None
        # to_relation_label : 宛先所属の表示用
        to_relation_label = None
        if inquiry.to_relation:
            if inquiry.to_authority_id == AUTHORITY_SHOP:
                to_relation_label = inquiry.to_relation.shop.shop_name
            elif inquiry.to_authority_id == AUTHORITY_WAREHOUSE:
                to_relation_label = inquiry.to_relation.warehouse.warehouse_name
        return render(request, self.template_name, {
            'inquiry': inquiry,
            'is_receiver': is_recv,
            'form': form,
            'to_relation_label': to_relation_label,
        })

    def post(self, request, pk, *args, **kwargs):
        inquiry, is_recv = self._get_inquiry_or_403(request, pk)
        if not is_recv:
            raise ForbiddenException
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

class InquiryCategoryListView(AdminRequiredMixin, TemplateView):
    template_name = 'inquiry/inquiry_category_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category_list'] = InquiryCategory.active_objects.order_by('category_name')
        return context
      
class InquiryCategoryCreateView(AdminRequiredMixin, CreateView):
    template_name = 'inquiry/inquiry_category_create.html'
    model = InquiryCategory
    form_class = InquiryCategoryForm
    success_url = reverse_lazy('inquiry_category_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '問い合わせカテゴリ作成'
        context['submit_label'] = '登録'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, '問い合わせカテゴリを登録しました。')
        return response

    def form_invalid(self, form):
        next_url = self.request.POST.get('next')
        if next_url:
            category_name_errors = form.errors.get('category_name')
            if category_name_errors:
                messages.error(self.request, category_name_errors[0])
            else:
                messages.error(self.request, '問い合わせカテゴリを登録できませんでした。')

            # open redirect チェック：内部リンクのみ許可
            parsed = urlparse(next_url)
            if not parsed.netloc and next_url.startswith('/'):
                return redirect(next_url)

        return super().form_invalid(form)

    def get_success_url(self):
        next_url = self.request.POST.get('next')
        if not next_url:
            return super().get_success_url()

        parsed_url = urlsplit(next_url)
        query_params = dict(parse_qsl(parsed_url.query, keep_blank_values=True))
        query_params['category_created'] = str(self.object.pk)
        return urlunsplit((
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            urlencode(query_params),
            parsed_url.fragment,
        ))

class InquiryCategoryUpdateView(AdminRequiredMixin, UpdateView):
    template_name = 'inquiry/inquiry_category_create.html'
    model = InquiryCategory
    form_class = InquiryCategoryForm
    success_url = reverse_lazy('inquiry_category_list')

    def get_queryset(self):
        return InquiryCategory.active_objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '問い合わせカテゴリ編集'
        context['submit_label'] = '更新'
        context['can_delete'] = not self.object.has_related_records()
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, '問い合わせカテゴリを更新しました。')
        return response


class InquiryCategoryDeleteView(AdminRequiredMixin, View):
    def post(self, request, pk):
        category = get_object_or_404(InquiryCategory.active_objects, pk=pk)

        if category.has_related_records():
            messages.error(
                request,
                '問い合わせに紐づくカテゴリのため削除できません。'
            )
        else:
            category.soft_delete()
            messages.success(request, '問い合わせカテゴリを削除しました。')

        # 共通処理：next URL の検証とリダイレクト
        next_url = request.POST.get('next')
        if next_url:
            parsed = urlparse(next_url)
            if not parsed.netloc and parsed.path.startswith('/'):
                return redirect(next_url)
        return redirect('inquiry_category_list')
