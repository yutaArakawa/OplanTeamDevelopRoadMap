from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Authority

User = get_user_model()

# 投入するAuthority マスタ
AUTHORITIES = [
    {'id': 1, 'authority_name': '管理者'},
    {'id': 2, 'authority_name': '店舗スタッフ'},
    {'id': 3, 'authority_name': '倉庫スタッフ'},
]

# 自動作成するスーパーユーザー（開発環境用）
SUPERUSER_USERNAME = 'admin'
SUPERUSER_PASSWORD = 'password'
SUPERUSER_GENDER   = 3   # その他
SUPERUSER_AUTHORITY_ID = 1


class Command(BaseCommand):
    help = 'Authorityマスタを投入し、スーパーユーザーを作成する（既存データはスキップ）'

    def handle(self, *args, **options):
        self._seed_authorities()
        self._create_superuser()

    # ------------------------------------------------------------------
    # Authority マスタ投入
    # ------------------------------------------------------------------
    def _seed_authorities(self):
        self.stdout.write('--- Authority マスタ投入 ---')
        for data in AUTHORITIES:
            _, created = Authority.objects.get_or_create(
                id=data['id'],
                defaults={'authority_name': data['authority_name']},
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  作成: id={data['id']} {data['authority_name']}"
                    )
                )
            else:
                self.stdout.write(
                    f"  スキップ: id={data['id']} {data['authority_name']} は既に存在します"
                )

    # ------------------------------------------------------------------
    # スーパーユーザー作成
    # ------------------------------------------------------------------
    def _create_superuser(self):
        self.stdout.write('--- スーパーユーザー作成 ---')
        if User.objects.filter(username=SUPERUSER_USERNAME).exists():
            self.stdout.write(
                f"  スキップ: ユーザー '{SUPERUSER_USERNAME}' は既に存在します"
            )
            return

        authority = Authority.objects.get(id=SUPERUSER_AUTHORITY_ID)
        User.objects.create_superuser(
            username=SUPERUSER_USERNAME,
            password=SUPERUSER_PASSWORD,
            user_gender=SUPERUSER_GENDER,
            authority=authority,
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"  作成: スーパーユーザー '{SUPERUSER_USERNAME}' を作成しました"
            )
        )
