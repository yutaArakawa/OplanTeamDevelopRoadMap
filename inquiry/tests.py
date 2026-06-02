import pytest
from django.urls import reverse
from inquiry.forms import InquiryCreateForm
from inquiry.models import Inquiry
from common.constants import AUTHORITY_SHOP, AUTHORITY_WAREHOUSE

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# 問い合わせ一覧
# ---------------------------------------------------------------------------

class TestInquiryList:

    def test_unauthenticated_redirect(self, client):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = client.get(reverse('inquiry_list'))
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_admin_sees_received_inquiries(self, client, admin_user, inquiry_to_admin):
        """管理者は受信一覧に自分宛の問い合わせが表示される"""
        client.force_login(admin_user)
        response = client.get(reverse('inquiry_list'))
        assert response.status_code == 200
        assert inquiry_to_admin in response.context['received_inquiries']

    def test_admin_no_sent_section(self, client, admin_user):
        """管理者は送信済み一覧セクションが表示されない（管理者は問い合わせ送信しない）"""
        client.force_login(admin_user)
        response = client.get(reverse('inquiry_list'))
        assert response.status_code == 200
        assert '送信済み一覧' not in response.content.decode()

    def test_shop_user_sees_received_inquiries(self, client, shop_user, inquiry_to_shop):
        """店舗スタッフは自分の店舗宛の問い合わせが受信一覧に表示される"""
        client.force_login(shop_user)
        response = client.get(reverse('inquiry_list'))
        assert response.status_code == 200
        assert inquiry_to_shop in response.context['received_inquiries']

    def test_warehouse_user_sees_received_inquiries(self, client, warehouse_user, inquiry_to_warehouse):
        """倉庫スタッフは自分の倉庫宛の問い合わせが受信一覧に表示される"""
        client.force_login(warehouse_user)
        response = client.get(reverse('inquiry_list'))
        assert response.status_code == 200
        assert inquiry_to_warehouse in response.context['received_inquiries']

    def test_shop_user_sees_sent_section(self, client, shop_user):
        """店舗スタッフは送信済み一覧セクションが表示される"""
        client.force_login(shop_user)
        response = client.get(reverse('inquiry_list'))
        assert response.status_code == 200
        assert '送信済み一覧' in response.content.decode()

    def test_warehouse_user_sees_sent_section(self, client, warehouse_user):
        """倉庫スタッフは送信済み一覧セクションが表示される"""
        client.force_login(warehouse_user)
        response = client.get(reverse('inquiry_list'))
        assert response.status_code == 200
        assert '送信済み一覧' in response.content.decode()

    def test_shop_user_sent_inquiries_appear(self, client, shop_user, inquiry_to_admin):
        """店舗スタッフが送信した問い合わせが送信済み一覧に表示される"""
        # inquiry_to_admin は shop_user が送信したもの
        client.force_login(shop_user)
        response = client.get(reverse('inquiry_list'))
        assert response.status_code == 200
        assert inquiry_to_admin in response.context['sent_inquiries']

    def test_status_filter_excludes_non_matching(self, client, admin_user, inquiry_to_admin):
        """ステータス絞り込みで一致しない問い合わせは受信一覧に表示されない"""
        client.force_login(admin_user)
        # inquiry_to_admin のステータスは PENDING(0)、COMPLETED(2) で絞ると非表示になる
        response = client.get(reverse('inquiry_list') + '?status=2')
        assert response.status_code == 200
        assert inquiry_to_admin not in response.context['received_inquiries']

    def test_status_filter_includes_matching(self, client, admin_user, inquiry_to_admin):
        """ステータス絞り込みで一致する問い合わせは受信一覧に表示される"""
        client.force_login(admin_user)
        # inquiry_to_admin のデフォルトステータスは PENDING(0)
        response = client.get(reverse('inquiry_list') + '?status=0')
        assert response.status_code == 200
        assert inquiry_to_admin in response.context['received_inquiries']


# ---------------------------------------------------------------------------
# 問い合わせ送信（ログイン済み・管理者以外）
# ---------------------------------------------------------------------------

class TestInquiryCreate:

    def test_unauthenticated_redirect(self, client):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = client.get(reverse('inquiry_create'))
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_admin_forbidden(self, client, admin_user):
        """管理者は問い合わせ送信画面にアクセスできない（403）"""
        client.force_login(admin_user)
        response = client.get(reverse('inquiry_create'))
        assert response.status_code == 403

    def test_shop_user_get_200(self, client, shop_user):
        """店舗スタッフは問い合わせ送信フォームを表示できる"""
        client.force_login(shop_user)
        response = client.get(reverse('inquiry_create'))
        assert response.status_code == 200
        assert 'form' in response.context

    def test_warehouse_user_get_200(self, client, warehouse_user):
        """倉庫スタッフは問い合わせ送信フォームを表示できる"""
        client.force_login(warehouse_user)
        response = client.get(reverse('inquiry_create'))
        assert response.status_code == 200
        assert 'form' in response.context

    def test_shop_user_post_to_admin_success(self, client, shop_user, authority_admin):
        """店舗スタッフが管理者宛に問い合わせを送信できる"""
        client.force_login(shop_user)
        response = client.post(reverse('inquiry_create'), {
            'to_authority': authority_admin.id,
            'to_relation': '',
            'inquiry_title': 'テスト件名',
            'inquiry_details': 'テスト問い合わせ内容',
        })
        assert response.status_code == 302
        assert response.url == reverse('inquiry_list')
        assert Inquiry.active_objects.filter(
            from_user=shop_user, to_authority=authority_admin
        ).exists()

    def test_missing_to_relation_validation_error(self, client, shop_user, authority_warehouse):
        """倉庫スタッフ宛送信時に to_relation を選択しないとバリデーションエラーになる"""
        client.force_login(shop_user)
        response = client.post(reverse('inquiry_create'), {
            'to_authority': authority_warehouse.id,
            'to_relation': '',
            'inquiry_details': 'バリデーションテスト',
        })
        assert response.status_code == 200
        assert response.context['form'].errors


# ---------------------------------------------------------------------------
# 問い合わせ送信（未ログインゲスト）
# ---------------------------------------------------------------------------

class TestInquiryGuestCreate:

    def test_get_200(self, client):
        """未ログインでもゲスト問い合わせフォームを表示できる"""
        response = client.get(reverse('inquiry_create_guest'))
        assert response.status_code == 200
        assert 'form' in response.context

    def test_logged_in_user_can_access(self, client, shop_user):
        """ログイン済みユーザーもゲスト問い合わせフォームを表示できる"""
        client.force_login(shop_user)
        response = client.get(reverse('inquiry_create_guest'))
        assert response.status_code == 200

    def test_post_success_redirects_to_guest_create(self, client, authority_admin, authority_shop):
        """有効なデータを送信すると管理者宛に問い合わせが作成されゲスト問い合わせ画面にリダイレクト"""
        response = client.post(reverse('inquiry_create_guest'), {
            'from_name': 'テストゲスト',
            'from_authority': authority_shop.id,
            'from_belong_shop': '',
            'from_belong_warehouse': '',
            'inquiry_title': 'ゲストテスト件名',
            'inquiry_details': 'ゲストテスト問い合わせ内容',
        })
        assert response.status_code == 302
        assert response.url == reverse('inquiry_create_guest')
        assert Inquiry.active_objects.filter(
            from_name='テストゲスト', to_authority=authority_admin
        ).exists()

    def test_post_missing_details_shows_error(self, client, authority_admin, authority_shop):
        """inquiry_details が空だとフォームエラーになり再表示される"""
        response = client.post(reverse('inquiry_create_guest'), {
            'from_name': 'テストゲスト',
            'from_authority': authority_shop.id,
            'from_belong_shop': '',
            'from_belong_warehouse': '',
            'inquiry_title': '',
            'inquiry_details': '',  # 必須フィールドが空
        })
        assert response.status_code == 200
        assert response.context['form'].errors


# ---------------------------------------------------------------------------
# 問い合わせ詳細・ステータス更新
# ---------------------------------------------------------------------------

class TestInquiryDetail:

    def test_unauthenticated_redirect(self, client, inquiry_to_admin):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = client.get(reverse('inquiry_detail', kwargs={'pk': inquiry_to_admin.pk}))
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_receiver_admin_can_access(self, client, admin_user, inquiry_to_admin):
        """受信者（管理者）は問い合わせ詳細を閲覧できる"""
        client.force_login(admin_user)
        response = client.get(reverse('inquiry_detail', kwargs={'pk': inquiry_to_admin.pk}))
        assert response.status_code == 200
        assert response.context['inquiry'] == inquiry_to_admin

    def test_sender_can_access(self, client, shop_user, inquiry_to_admin):
        """送信者は問い合わせ詳細を閲覧できる"""
        client.force_login(shop_user)
        response = client.get(reverse('inquiry_detail', kwargs={'pk': inquiry_to_admin.pk}))
        assert response.status_code == 200

    def test_unrelated_user_forbidden(self, client, warehouse_user, inquiry_to_admin):
        """送受信者でないユーザーは403エラーになる"""
        # inquiry_to_admin は admin 宛、from_user は shop_user
        # warehouse_user はどちらでもないため 403
        client.force_login(warehouse_user)
        response = client.get(reverse('inquiry_detail', kwargs={'pk': inquiry_to_admin.pk}))
        assert response.status_code == 403

    def test_receiver_sees_status_form(self, client, admin_user, inquiry_to_admin):
        """受信者はステータス更新フォームが表示される"""
        client.force_login(admin_user)
        response = client.get(reverse('inquiry_detail', kwargs={'pk': inquiry_to_admin.pk}))
        assert response.status_code == 200
        assert response.context['is_receiver'] is True
        assert response.context['form'] is not None

    def test_sender_no_status_form(self, client, shop_user, inquiry_to_admin):
        """送信者はステータス更新フォームが表示されない"""
        client.force_login(shop_user)
        response = client.get(reverse('inquiry_detail', kwargs={'pk': inquiry_to_admin.pk}))
        assert response.status_code == 200
        assert response.context['is_receiver'] is False
        assert response.context['form'] is None

    def test_receiver_can_update_status(self, client, admin_user, inquiry_to_admin):
        """受信者はステータスを更新できる"""
        client.force_login(admin_user)
        response = client.post(
            reverse('inquiry_detail', kwargs={'pk': inquiry_to_admin.pk}),
            {'status': Inquiry.Status.IN_PROGRESS},
        )
        assert response.status_code == 302
        inquiry_to_admin.refresh_from_db()
        assert inquiry_to_admin.status == Inquiry.Status.IN_PROGRESS

    def test_sender_cannot_post_status(self, client, shop_user, inquiry_to_admin):
        """送信者がステータス更新POSTを送ると403エラーになる"""
        client.force_login(shop_user)
        response = client.post(
            reverse('inquiry_detail', kwargs={'pk': inquiry_to_admin.pk}),
            {'status': Inquiry.Status.IN_PROGRESS},
        )
        assert response.status_code == 403

    def test_shop_receiver_can_access(self, client, shop_user, inquiry_to_shop):
        """受信者（店舗スタッフ）は自分の店舗宛の問い合わせを閲覧できる"""
        client.force_login(shop_user)
        response = client.get(reverse('inquiry_detail', kwargs={'pk': inquiry_to_shop.pk}))
        assert response.status_code == 200
        assert response.context['is_receiver'] is True

    def test_warehouse_receiver_can_access(self, client, warehouse_user, inquiry_to_warehouse):
        """受信者（倉庫スタッフ）は自分の倉庫宛の問い合わせを閲覧できる"""
        client.force_login(warehouse_user)
        response = client.get(reverse('inquiry_detail', kwargs={'pk': inquiry_to_warehouse.pk}))
        assert response.status_code == 200
        assert response.context['is_receiver'] is True


# ---------------------------------------------------------------------------
# 問い合わせ削除（論理削除）
# ---------------------------------------------------------------------------

class TestInquiryDelete:

    def test_unauthenticated_redirect(self, client, inquiry_to_admin):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = client.post(reverse('inquiry_delete', kwargs={'pk': inquiry_to_admin.pk}))
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_delete_sets_delete_flag(self, client, admin_user, inquiry_to_admin):
        """削除するとdelete_flgがTrueになる"""
        client.force_login(admin_user)
        client.post(reverse('inquiry_delete', kwargs={'pk': inquiry_to_admin.pk}))
        inquiry_to_admin.refresh_from_db()
        assert inquiry_to_admin.delete_flg is True

    def test_deleted_not_in_active_objects(self, client, admin_user, inquiry_to_admin):
        """削除後はactive_objectsに含まれない"""
        client.force_login(admin_user)
        client.post(reverse('inquiry_delete', kwargs={'pk': inquiry_to_admin.pk}))
        assert not Inquiry.active_objects.filter(pk=inquiry_to_admin.pk).exists()

    def test_delete_redirects_to_list(self, client, admin_user, inquiry_to_admin):
        """削除後は問い合わせ一覧にリダイレクトされる"""
        client.force_login(admin_user)
        response = client.post(reverse('inquiry_delete', kwargs={'pk': inquiry_to_admin.pk}))
        assert response.status_code == 302
        assert response.url == reverse('inquiry_list')

    def test_sender_can_delete_own_inquiry(self, client, shop_user, inquiry_to_admin):
        """送信者は自分の問い合わせを削除できる"""
        client.force_login(shop_user)
        client.post(reverse('inquiry_delete', kwargs={'pk': inquiry_to_admin.pk}))
        inquiry_to_admin.refresh_from_db()
        assert inquiry_to_admin.delete_flg is True


# ---------------------------------------------------------------------------
# フォーム直接テスト（label_from_instance / 初期値プリセット）
# ---------------------------------------------------------------------------

class TestInquiryCreateFormBehavior:

    def test_shop_user_to_relation_label_shows_warehouse_name(self, shop_user, relation):
        """店舗スタッフの場合、to_relation の選択肢ラベルは倉庫名のみ表示される"""
        form = InquiryCreateForm(login_user=shop_user)
        field = form.fields['to_relation']
        label = field.label_from_instance(relation)
        assert label == relation.warehouse.warehouse_name

    def test_warehouse_user_to_relation_label_shows_shop_name(self, warehouse_user, relation):
        """倉庫スタッフの場合、to_relation の選択肢ラベルは店舗名のみ表示される"""
        form = InquiryCreateForm(login_user=warehouse_user)
        field = form.fields['to_relation']
        label = field.label_from_instance(relation)
        assert label == relation.shop.shop_name

    def test_shop_user_relation_id_prepopulates_to_authority_and_to_relation(self, shop_user, relation):
        """店舗スタッフが relation_id を渡すと宛先権限=倉庫スタッフ・宛先所属が初期入力される"""
        form = InquiryCreateForm(login_user=shop_user, relation_id=relation.id)
        assert form.initial.get('to_authority') == AUTHORITY_WAREHOUSE
        assert form.initial.get('to_relation') == relation.pk

    def test_warehouse_user_relation_id_prepopulates_to_authority_and_to_relation(self, warehouse_user, relation):
        """倉庫スタッフが relation_id を渡すと宛先権限=店舗スタッフ・宛先所属が初期入力される"""
        form = InquiryCreateForm(login_user=warehouse_user, relation_id=relation.id)
        assert form.initial.get('to_authority') == AUTHORITY_SHOP
        assert form.initial.get('to_relation') == relation.pk

    def test_no_relation_id_no_prepopulation(self, shop_user):
        """relation_id を渡さない場合は初期入力されない"""
        form = InquiryCreateForm(login_user=shop_user)
        assert 'to_authority' not in form.initial
        assert 'to_relation' not in form.initial

    def test_relation_belonging_to_different_shop_no_prepopulation(self, shop_user, shop2, warehouse):
        """自分の店舗と関係ない relation_id を渡しても初期入力されない"""
        from inventory.models import Relation
        other_relation = Relation.objects.create(shop=shop2, warehouse=warehouse)
        form = InquiryCreateForm(login_user=shop_user, relation_id=other_relation.id)
        assert 'to_authority' not in form.initial
        assert 'to_relation' not in form.initial

    def test_nonexistent_relation_id_no_prepopulation(self, shop_user):
        """存在しない relation_id を渡しても初期入力されずエラーにならない"""
        form = InquiryCreateForm(login_user=shop_user, relation_id=99999)
        assert 'to_authority' not in form.initial
        assert 'to_relation' not in form.initial


# ---------------------------------------------------------------------------
# 問い合わせ送信画面 GET に relation クエリパラメータを渡すテスト
# ---------------------------------------------------------------------------

class TestInquiryCreateViewRelationParam:

    def test_shop_user_get_with_relation_param_prepopulates_form(self, client, shop_user, relation):
        """店舗スタッフが ?relation=<id> 付きで GET すると、フォームに初期値が入る"""
        client.force_login(shop_user)
        url = reverse('inquiry_create') + f'?relation={relation.id}'
        response = client.get(url)
        assert response.status_code == 200
        form = response.context['form']
        assert form.initial.get('to_authority') == AUTHORITY_WAREHOUSE
        assert form.initial.get('to_relation') == relation.pk

    def test_warehouse_user_get_with_relation_param_prepopulates_form(self, client, warehouse_user, relation):
        """倉庫スタッフが ?relation=<id> 付きで GET すると、フォームに初期値が入る"""
        client.force_login(warehouse_user)
        url = reverse('inquiry_create') + f'?relation={relation.id}'
        response = client.get(url)
        assert response.status_code == 200
        form = response.context['form']
        assert form.initial.get('to_authority') == AUTHORITY_SHOP
        assert form.initial.get('to_relation') == relation.pk

    def test_get_without_relation_param_no_prepopulation(self, client, shop_user):
        """relation クエリパラメータなしで GET すると初期値は空"""
        client.force_login(shop_user)
        response = client.get(reverse('inquiry_create'))
        assert response.status_code == 200
        form = response.context['form']
        assert 'to_authority' not in form.initial
        assert 'to_relation' not in form.initial

    def test_get_with_nonexistent_relation_param_returns_200(self, client, shop_user):
        """存在しない relation id を渡しても 200 で表示される（初期値なし）"""
        client.force_login(shop_user)
        url = reverse('inquiry_create') + '?relation=99999'
        response = client.get(url)
        assert response.status_code == 200
        form = response.context['form']
        assert 'to_authority' not in form.initial
        assert 'to_relation' not in form.initial
