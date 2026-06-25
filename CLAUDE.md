# CLAUDE.md

このファイルはリポジトリ内のコードを扱う際にClaude Code（claude.ai/code）へ提供するガイダンスです。

詳細は以下のファイルを参照してください：
- `frontend/CLAUDE.md` — React のガイドライン・パターン
- `docs/claude/django-features.md` — Django 各機能の詳細フロー
- `docs/claude/django-patterns.md` — コーディングパターン・URL規則・スタイリング
- `docs/claude/batch.md` — バッチ処理・デプロイ注意事項

---

## 開発環境

このプロジェクトはDocker ComposeとMySQLを使用しています。Docker Composeファイルは2種類あります：

- `docker-compose.dev.yml` — 開発環境：nginx（80番ポート）→ Gunicorn → Django
- `docker-compose.prod.yml` — 本番環境：nginx（9149番ポート）→ Gunicorn → Django

**環境変数のセットアップ（初回必須）：**
`.env.example` をコピーして `.env` を作成し、値はチームメンバーから入手してください。
```bash
cp .env.example .env
```
`settings.py` は `django-environ` を使って `.env` から `SECRET_KEY`・`DEBUG`・`ALLOWED_HOSTS`・DB接続情報を読み込みます。

**開発環境（ローカル）：**
```bash
docker compose -f docker-compose.dev.yml up
```
Webサーバーは `http://localhost`（ポート80）で起動します。MySQLデータベースはポート3307（コンテナ内の3306番ポートにマッピング）で公開されます。

**本番環境：**
```bash
docker compose -f docker-compose.prod.yml up -d --build
```
Webサーバーはnginx経由で `http://localhost:9149` で起動します。

DockerなしのローカルCI環境（SQLiteを使用）：

```bash
pip install -r requirements.txt
CI=true python manage.py migrate
CI=true python manage.py runserver
```

---

## よく使うコマンド

```bash
# 全テスト実行（高速 — DockerなしでSQLiteを使用）
CI=true pytest

# 全テスト実行（Dockerのdevコンテナ内）
docker exec -e CI=true python_stock_app-web-1 pytest

# 特定のアプリのみテスト実行
CI=true pytest accounts/

# 特定のテストクラスやメソッドのみ実行
CI=true pytest accounts/tests.py::TestLogin
CI=true pytest accounts/tests.py::TestLogin::test_login_success

# マイグレーション実行
python manage.py migrate

# スーパーユーザー作成（DBにAuthority id=1が存在する必要あり）
python manage.py createsuperuser
```

---

## アーキテクチャ概要

このシステムは複数拠点の小売業向けDjango在庫管理システムです。倉庫と店舗の関係、在庫数、発注、ユーザーアカウントを管理します。

**アプリ構成：**

- `inventory` — コアドメインモデル：`Warehouse`、`Shop`、`Goods`、`GoodsCategory`、`ShopStock`、`WarehouseStock`、`Relation`（倉庫↔店舗のリンク）、`Order`、`OrderGoods`
- `accounts` — `AbstractUser`を拡張したカスタムユーザーモデル。`Authority`（権限）と`Warehouse`/`Shop`へのFKを持つ
- `dashboard` — ホーム画面ビュー；`MonthlyOrderSummary`集計モデル
- `inquiry` — ユーザーロール間の問い合わせ/サポートチケットモデル
- `common` — 共通ユーティリティ：`BaseModel`、`ActiveManager`、権限チェックMixin、定数、コンテキストプロセッサ。オートコンプリートAPIエンドポイント（`/common/api/shops/autocomplete/`、`/common/api/warehouses/autocomplete/`）をDjango REST Framework（`djangorestframework`）で提供。シリアライザーは`common/seializers.py`、ビューは`common/views.py`、URLは`config/urls.py`で`common/`プレフィックスで登録。

**データベース**：Docker内のMySQL（`stockdb`）。CIはSQLiteを使用（`config/settings.py`の`CI`環境変数で制御）。

---

## CI / テスト

**CI**：CircleCIがpushごとにマイグレーションと`pytest`を実行。

**テスト**：pytest + pytest-djangoを使用。設定は`pytest.ini`（`DJANGO_SETTINGS_MODULE`を設定）。共通フィクスチャ（ユーザー、権限、店舗、倉庫）はプロジェクトルートの`conftest.py`に定義。各`Authority`フィクスチャはロール定数（`AUTHORITY_ADMIN=1`、`AUTHORITY_SHOP=2`、`AUTHORITY_WAREHOUSE=3`）に一致する明示的な`id`で作成し、テスト中のビューとフォームの権限ロジックが正しく動作するようにする。

アプリごとのテストファイル：
- `accounts/tests.py` — ログイン、ユーザーCRUD（管理者）、ユーザー管理
- `dashboard/tests.py` — 全3権限のDashboardView；発注ランキングのサービス層テスト
- `inventory/tests/test_goods_category.py` — GoodsCategoryの一覧/作成/更新/削除
- `inventory/tests/test_goods.py` — 商品の一覧/作成/更新/削除
- `inventory/tests/test_warehouse.py` — 倉庫マスタCRUD、倉庫在庫一覧/編集、受注一覧/ステータス更新/CSV/PDFエクスポート
- `inventory/tests/test_shop.py` — 店舗マスタCRUD、店舗在庫一覧/編集、店舗削除
- `inventory/tests/test_order.py` — 発注商品一覧、発注作成、CSVダウンロード/インポート、発注履歴、CSV/PDFエクスポート
- `inventory/tests/test_relation.py` — 連携一覧/作成/削除、店舗連携倉庫一覧
- `inquiry/tests.py` — 問い合わせ一覧/作成/詳細/削除、InquiryCategory CRUD、合計66テスト
- `common/tests.py` — 店舗名・倉庫名オートコンプリートAPIテスト

CircleCIの詳細設定（並列実行・キャッシュ・カバレッジ等）は `.circleci/config.yml` を参照。
