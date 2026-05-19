from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from accounts.models import Authority

User = get_user_model()

# Create your tests here.

class LoginTest(TestCase):

    def setUp(self):
        # Authorityを作成
        self.authority = Authority.objects.create(
            authority_name='管理者'
        )
        # テスト用ユーザー作成
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword',
            user_gender=1,
            authority=self.authority
        )
        self.url = reverse('login')
    
    # ログインページが表示されるか
    def test_login_page_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    # 正しいID/PWでログインできるか
    def test_login_success(self):
        response = self.client.post(self.url, {
            'username': 'testuser',
            'password': 'testpassword'
        })
        self.assertRedirects(response, '/')

    # 間違ったPWで弾かれるか
    def test_login_fail_wrong_password(self):
        response = self.client.post(self.url, {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)  # リダイレクトせず同じページに留まる
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    # 存在しないユーザーで弾かれるか
    def test_login_fail_unknown_user(self):
        response = self.client.post(self.url, {
            'username': 'nobody',
            'password': 'testpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)