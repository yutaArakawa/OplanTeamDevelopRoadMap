# CLAUDE.md

このファイルはリポジトリ内のコードを扱う際にClaude Code（claude.ai/code）へ提供するガイダンスです。

## 開発環境

このプロジェクトはDocker ComposeとMySQLを使用しています。Docker Composeファイルは2種類あります：

- `docker-compose.dev.yml` — 開発環境：Gunicornを8000番ポートで直接起動
- `docker-compose.prod.yml` — 本番環境：nginx（9149番ポート）→ Gunicorn → Django

**開発環境（ローカル）：**
```bash
docker-compose -f docker-compose.dev.yml up
```
Webサーバーは `http://localhost:8000` で起動します。MySQLデータベースはポート3307（コンテナ内の3306番ポートにマッピング）で公開されます。

**本番環境：**
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```
Webサーバーはnginx経由で `http://localhost:9149` で起動します。

DockerなしのローカルCI環境（SQLiteを使用）：

```bash
pip install -r requirements.txt
CI=true python manage.py migrate
CI=true python manage.py runserver
```

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

## アーキテクチャ概要

このシステムは複数拠点の小売業向けDjango在庫管理システムです。倉庫と店舗の関係、在庫数、発注、ユーザーアカウントを管理します。

**アプリ構成：**

- `inventory` — コアドメインモデル：`Warehouse`、`Shop`、`Goods`、`GoodsCategory`、`ShopStock`、`WarehouseStock`、`Relation`（倉庫↔店舗のリンク）、`Order`、`OrderGoods`
- `accounts` — `AbstractUser`を拡張したカスタムユーザーモデル。`Authority`（権限）と`Warehouse`/`Shop`へのFKを持つ
- `dashboard` — ホーム画面ビュー；`MonthlyOrderSummary`集計モデル
- `inquiry` — ユーザーロール間の問い合わせ/サポートチケットモデル
- `common` — 共通ユーティリティ：`BaseModel`、`ActiveManager`、権限チェックMixin、定数、コンテキストプロセッサ。オートコンプリートAPIエンドポイント（`/common/api/shops/autocomplete/`、`/common/api/warehouses/autocomplete/`）をDjango REST Framework（`djangorestframework`）で提供。シリアライザーは`common/seializers.py`、ビューは`common/views.py`、URLは`config/urls.py`で`common/`プレフィックスで登録。

**ダッシュボード（ホーム画面）：**

- **管理者**：サマリー件数（倉庫、店舗、商品、カテゴリ、ユーザー、発注中の注文）
- **店舗スタッフ**：
  - **自店舗 発注ランキング** — 前日に自店舗が発注した商品トップ10。`MonthlyOrderSummary`から`services.get_monthly_order_summary()`と`services.get_order_ranking()`で集計
  - **全店舗 発注ランキング** — 前日に全店舗で発注された商品トップ10
- **倉庫スタッフ**：在庫件数（自倉庫の在庫数、新規/準備中の注文件数）と倉庫在庫一覧

**発注フロー（店舗スタッフ）：**

1. **発注商品選択画面** (`order_goods_list`, `OrderGoodsListView`) — 店舗スタッフが発注する商品を選択。連携倉庫の在庫合計でアノテーションされた有効商品一覧を表示。カテゴリフィルター対応。
2. **発注画面** (`order_create/<goods_pk>/`, `OrderCreateView`) — 店舗スタッフが倉庫ごとの発注数を入力。POSTで`quantity > 0`の倉庫ごとに`Order`を1件作成し、紐づく`OrderGoods`レコードも作成。
3. **CSV一括発注ダウンロード** (`order_csv_download`, `OrderCsvDownloadView`) — 連携倉庫の在庫データを事前入力したCSVテンプレートをダウンロード（列：倉庫ID、倉庫名、カテゴリ、商品ID、商品名、現在の在庫数、発注数）。発注数列は空欄。
4. **CSV一括発注インポート** (`order_csv_import`, `OrderCsvImportView`) — 入力済みCSVをPOSTで受け付け。発注数が空または0の行はスキップ。同じ倉庫への複数商品は1件の`Order`にまとめる（インポートごとに倉庫1件につき`Order`1件）。

**発注履歴フロー（店舗スタッフ）：**

5. **発注履歴画面** (`order_history`, `OrderHistoryView`) — 店舗スタッフが自店舗の発注履歴を閲覧。注文ごとに関連商品をまとめて表示。日付範囲とステータスでフィルター対応。共有クエリ/行ロジックに`services.get_order_history_data(shop)`と`services.build_rows(orders)`を使用。
6. **発注履歴CSVエクスポート** (`order_history_csv_export`, `OrderHistoryCSVExportView`) — 日付/ステータスフィルターを適用した発注履歴をCSVでダウンロード。列：発注先倉庫、商品名、発注個数、ステータス、発注日時、更新日時。BOMは`charset=utf-8`で`response.write('﻿')`を使って手動書き込み（`charset=utf-8-sig`はwrite()のたびにBOMが挿入されるため使用禁止）。
7. **発注履歴PDFエクスポート** (`order_history_pdf_export`, `OrderHistoryPDFExportView`) — reportlabとHeiseiKakuGo-W5日本語フォントを使って発注履歴をPDFでダウンロード。

**店舗在庫管理フロー（店舗スタッフ）：**

- **店舗在庫一覧** (`shop_stock_list`, `ShopStockListView`) — 店舗スタッフが有効な全商品と自店舗の現在在庫数を閲覧。`ShopStock`レコードがない商品は`Coalesce(Sum(...), 0)`で0表示。カテゴリフィルター対応。
- **店舗在庫編集** (`shop_stock_edit/<goods_pk>/`, `ShopStockEditView`) — 特定商品の在庫数を更新。`ShopStock.objects.update_or_create()`を使用するため新規作成と更新の両方を同じPOSTで処理。不明な`goods_pk`は404を返す。

**マスタデータ管理（管理者のみ）：**

- **GoodsCategory CRUD** (`goods_category_list/create/<pk>/edit/<pk>/delete/`) — 管理者が商品カテゴリを管理。`GoodsCategoryCreateView.form_invalid()`が`next`パラメータのリダイレクトを処理（商品フォームからの作成時に使用）。`get_success_url()`が`next`に`?category_created=<pk>`を付加することで商品フォームが新カテゴリを事前選択できる。
- **Goods CRUD** (`goods_list/create/<pk>/edit/<pk>/delete/`) — 管理者が商品を管理。`GoodsCreateView`/`GoodsUpdateView`は`get_initial()`でGETパラメータから`?category_created=<pk>`を読み取り、インライン作成後のカテゴリフィールドを事前入力。`GoodsCreateView.form_valid()`では**初期在庫レコードが自動作成**される：`services.insert_initial_warehouse_stock_for_goods()`と`services.insert_initial_shop_stock_for_goods()`で全有効倉庫・店舗に`stock=0`の`WarehouseStock`/`ShopStock`レコードを作成。`transaction.atomic()` + `select_for_update()`で整合性を保ち、ユニーク制約付きの`get_or_create()`で同時作成時の重複を防止。**商品削除**：`Goods.has_related_records()`は`stock__gt=0`の在庫レコード（単なる存在ではなく）と`OrderGoods`の存在をチェック。これにより作成直後の在庫ゼロ商品の削除が可能。
- **Warehouse CRUD** (`warehouses/`, `warehouses/create/`, `warehouses/<pk>/edit/`, `warehouses/<pk>/delete/`) — 管理者が倉庫を管理。`WarehouseUpdateView`は`can_delete`コンテキストを提供（倉庫にユーザー・在庫・連携がある場合はFalse）。
- **Shop CRUD** (`shops/`, `shops/create/`, `shops/<pk>/edit/`, `shops/<pk>/delete/`) — 管理者が店舗を管理。`ShopUpdateView`は`can_delete`コンテキストを提供（店舗にユーザー・在庫・連携・月次サマリーがある場合はFalse）。
- **Relation CRUD** (`relations/`, `relations/create/`, `relations/<pk>/delete/`) — 管理者が倉庫↔店舗の連携を管理。`RelationForm.clean()`で同じ店舗・倉庫ペアの有効な重複連携を防止。

**受注管理フロー（倉庫スタッフ）：**

- **受注管理一覧** (`warehouse_orders/`, `WarehouseOrderListView`) — 倉庫スタッフが自倉庫への受注を閲覧。日付範囲とステータスでフィルター対応。モジュールレベルのヘルパー`_get_filtered_orders()`と`_build_rows()`を使用。
- **受注ステータス更新** (`warehouse_orders/<pk>/status/`, `WarehouseOrderStatusUpdateView`) — 倉庫スタッフが受注ステータスを更新。`ORDERED(0)`と`PREPARING(1)`のみ受付（`ALLOWED_STATUSES`）；それ以外はエラーを返す。ログイン中の倉庫に属さない注文は404を返す。
- **受注CSVエクスポート** (`warehouse_orders/export/csv/`, `WarehouseOrderCSVExportView`) — 受注をCSVでダウンロード。`content_type='text/csv; charset=utf-8-sig'`を使用（DjangoはutF-8-sigで各`write()`呼び出しをエンコードし、全行にBOMを付加することに注意）。列：発注元店舗、商品名、発注個数、ステータス、発注日時、更新日時。
- **受注PDFエクスポート** (`warehouse_orders/export/pdf/`, `WarehouseOrderPDFExportView`) — reportlabを使って受注をPDFでダウンロード。

**店舗の連携倉庫一覧：**

- **連携倉庫一覧** (`shop/connected-warehouses/`, `ShopConnectedWarehouseListView`) — 店舗スタッフが自店舗に連携された倉庫を閲覧。`?relation=<id>`で問い合わせ作成へのエントリーポイントとして使用。

**問い合わせフロー：**

- **問い合わせ一覧** (`inquiry_list`, `InquiryListView`) — 受信・送信済みの問い合わせを表示。受信一覧はログインユーザーの権限と所属（店舗または倉庫）でフィルター。管理者は管理者権限宛の全問い合わせを閲覧；店舗/倉庫スタッフは`to_relation`で自拠点宛のみ閲覧。権限（`authority=guest`のゲストクエリ含む）、店舗、倉庫、ステータスでフィルター対応。**ゲスト問い合わせ**（`from_user=NULL`かつ`from_authority=NULL`）は`Inquiry.get_from_authority_display()`で「ゲスト」と表示。
- **問い合わせ送信** (`inquiry_create`, `InquiryCreateView`) — ログイン済みの非管理者ユーザー向け。`to_relation`フィールドはユーザーの店舗/倉庫に連携された関係のみ表示；`label_from_instance`で相手方名のみ表示（店舗スタッフは倉庫名、倉庫スタッフは店舗名）。`?relation=<id>`クエリパラメータ（連携倉庫一覧ページからなど）で`to_authority`と`to_relation`を事前入力。
- **ゲスト問い合わせ** (`inquiry_create_guest`, `InquiryGuestCreateView`) — 未認証ユーザー向け；常に管理者権限宛に送信。
- **問い合わせ詳細・ステータス更新** (`inquiry_detail/<pk>/`, `InquiryDetailView`) — 受信者はステータス更新可（未対応/対応中/対応済み）；送信者は閲覧のみ。
- **論理削除** (`inquiry_delete/<pk>/`, `InquiryDeleteView`) — 送信者または受信者が論理削除（`delete_flg=True`）可能。

**問い合わせカテゴリ管理（管理者のみ）：**

- **InquiryCategoryモデル** — 問い合わせを分類。ソフトデリート対応のため`BaseModel`を継承。`condition=Q(delete_flg=False)`付きの`UniqueConstraint`とモデルレベルの`clean()`バリデーションでカテゴリ名のユニーク制約を適用（大文字小文字区別、未削除レコードのみ）。削除前に問い合わせとの紐づきを確認する`has_related_records()`メソッドを提供。
- **カテゴリ一覧** (`categories/`, `inquiry_category_list`, `InquiryCategoryListView`) — 管理者専用ビュー。有効な問い合わせカテゴリを名前順で一覧表示。
- **カテゴリ作成** (`categories/create/`, `inquiry_category_create`, `InquiryCategoryCreateView`) — 管理者が新カテゴリを作成。`next`パラメータによるインライン作成対応（GoodsCategoryと同パターン）：`next=<url>`付きのフォーム送信でリダイレクトURLに`?category_created=<pk>`を付加し、親フォーム（問い合わせ作成など）で新カテゴリを事前選択可能。
- **カテゴリ編集** (`categories/<pk>/edit/`, `inquiry_category_edit`, `InquiryCategoryUpdateView`) — 管理者がカテゴリ名を更新。テンプレートに`can_delete`コンテキストフラグを表示（問い合わせに紐づくカテゴリはFalse）。
- **カテゴリ削除** (`categories/<pk>/delete/`, `inquiry_category_delete`, `InquiryCategoryDeleteView`) — 管理者がカテゴリを論理削除。削除前に`has_related_records()`をチェック；関連問い合わせが存在する場合はエラーメッセージを表示して削除せずリダイレクト。
- **カテゴリ選択（問い合わせ作成時）** — `InquiryCreateView`と`InquiryGuestCreateView`はいずれも`inquiry_category`を必須フィールドとして含む。問い合わせ作成時にカテゴリの選択が必須。フォームはカテゴリフィールドを`form-select`（Bootstrap）でレンダリング。
- **カテゴリフィルター（問い合わせ一覧）** — `InquiryListView`は`?category=<id>`クエリパラメータで受信・送信両方の問い合わせをカテゴリフィルター対応。フィルターUI用に全有効カテゴリを`categories`としてテンプレートコンテキストに渡す。

**主要パターン：**

- **論理削除**：全モデルは`delete_flg`を持つ`BaseModel`を継承。通常のクエリは`Model.active_objects`（`delete_flg=False`でフィルター）；`Model.objects`は削除済みを含む全レコードを返す。
- **ロールベースアクセス制御**：`common/constants.py`で3つのロールを定義 — `AUTHORITY_ADMIN=1`、`AUTHORITY_SHOP=2`、`AUTHORITY_WAREHOUSE=3`。アクセス制御は`common/mixins.py`のMixin（`AdminRequiredMixin`、`ShopStaffRequiredMixin`、`WarehouseStaffRequiredMixin`）を使用。定数は`authority_constants`コンテキストプロセッサで全テンプレートに注入。
- **ユーザー制約**：店舗スタッフ（`authority_id=2`）は`shop` FKが必須；倉庫スタッフ（`authority_id=3`）は`warehouse` FKが必須。`User.clean()`で強制。
- **アプリ間FK参照**：`accounts.User`は`inventory.Warehouse`と`inventory.Shop`を文字列（`'inventory.Warehouse'`）で参照。`dashboard.MonthlyOrderSummary`も同様。循環インポートを避けるため文字列形式のFKターゲットを使用。
- **services.py**：複数ビューで共有するビジネスロジックは`<app>/services.py`に配置。ビューはHTTPのみ担当（リクエスト解析、レンダリング、リダイレクト）；サービスはクエリセット構築、フィルタリング、データ変換を担当。例：`inventory/services.py`には`get_order_history_data()`、`order_filter_by_date_and_status()`、`build_rows()`、`get_shop_stock_list()`、`update_or_create_shop_stock()`など；`dashboard/services.py`には`get_monthly_order_summary(date, shop=None)`（日付/店舗でフィルターしてQuerySetを返す）と`get_order_ranking(summary_queryset, limit=10)`（QuerySetを受け取り商品ごとに集計してランキングデータをvalues形式で返す）。CSVエクスポートはBOMを`charset=utf-8`で`response.write('﻿')`を使って手動書き込み（`charset=utf-8-sig`はwrite()のたびにBOMが挿入されてファイルが破損するため使用禁止）。
- **label_from_instance**：`ModelChoiceField`の`field.label_from_instance = lambda obj: ...`でフィールドをサブクラス化せずに各選択肢の表示テキストをカスタマイズ。`queryset`代入後に設定すること。
- **クエリパラメータによるフォーム事前入力**：URLにクエリパラメータを付加して一覧画面から作成フォームにデータを渡す（例：`?relation=<id>`）。ビューで`request.GET.get('relation')`を読み取りフォームの`__init__`に渡す；フォームは`self.initial[field]`で特定フィールドを事前入力。
- **update_or_create によるアップサート**：POSTで新規作成と既存レコード更新を透過的に処理する場合は`Model.objects.update_or_create(lookup_fields, defaults={...})`を使用（例：`ShopStockEditView`）。
- **ゲストエンティティ処理**：ゲスト/未認証の送信を表すモデル（例：`InquiryGuestCreateView`からの`Inquiry`）は`from_user=NULL`と`from_authority=NULL`でゲストレコードを識別。両ForeignKeyフィールドがNULLの場合に人間が読めるラベル（「ゲスト」）を返す`get_*_display()`メソッド（例：`get_from_authority_display()`）を提供。ビューとテンプレートは特別なクエリ値（例：`authority=guest`）でフィルター可能；ビューは`filter(from_user__isnull=True, from_authority__isnull=True)`に変換。

**フロントエンドスタイリング：**

- **Bootstrapを優先**：可能な限りBootstrapのユーティリティクラスとコンポーネントを使用。
- **カスタムCSS**：Bootstrapで対応できない場合（グラデーション、特定の`rgba`色、`letter-spacing`、ホバートランジションなど）は外部`.css`ファイルにCSSを記述 — HTML要素へのインライン`style=""`属性、テンプレート内の`<style>`ブロックは使用禁止。
- **静的ファイルの配置**：CSS/JSは全てプロジェクト直下の`static/`ディレクトリにアプリ名ごとに配置 — 例：`static/accounts/css/accounts.css`、`static/inventory/css/inventory.css`。共通CSS/JSは`static/common/css/common.css`と`static/common/js/common.js`に配置。`{% load static %}`と`<link rel="stylesheet" href="{% static '...' %}">`でファイルを読み込む。`collectstatic`は使用しない；nginxが`./static`を直接マウントして配信。
- **STATIC_URL**：`settings.py`で`'/static/'`（先頭スラッシュあり）に設定すること。`{% static %}`がURLの深さに関わらず全ページで正しく解決できる絶対パスを生成するために必要。
- **ページ固有CSS**：`base.html`を継承するテンプレートでページ固有のCSSファイルを読み込む場合は`{% block extra_css %}`を使用：
  ```html
  {% load static %}
  {% block extra_css %}
  <link rel="stylesheet" href="{% static 'app/css/app.css' %}">
  {% endblock %}
  ```

**URL規則：**

- **リソース名は複数形**：コレクションは複数形 — `warehouses/`、`shops/`、`orders/`など。
- **URLパスはハイフン区切り**：複数単語はハイフンで接続 — `status-update`、`connected-warehouses`。
- **`name=`はアンダースコア区切り**：`name=`パラメータはPython識別子規則に従う — `warehouse_order_status_update`。
- **静的パスを変数パスより前に**：同じリソースグループ内では静的パス（例：`warehouses/stock/`）を変数パス（例：`warehouses/<int:pk>/edit/`）より前に配置。
- **標準CRUDパターン**：
  ```
  <resource>/                 一覧
  <resource>/create/          作成
  <resource>/<pk>/edit/       編集
  <resource>/<pk>/delete/     削除
  ```

**データベース**：Docker内のMySQL（`stockdb`）。CIはSQLiteを使用（`config/settings.py`の`CI`環境変数で制御）。

**CI**：CircleCIがpushごとにマイグレーションと`pytest`を実行。

**CircleCI設定**（`.circleci/config.yml`）：
- **並列実行**：4コンテナでテストを並列実行して高速なフィードバック
- **テスト分散**：`pytest-split` v0.11.0が過去の実行時間をもとにテストを均等配分。オプション：`--splits=4 --group=$((CIRCLE_NODE_INDEX + 1)) --splitting-algorithm=least_duration --durations-path=.circleci/.test_durations --store-durations`。初回はタイミングデータなしで均等配分；以降は`.circleci/.test_durations`で最適配分。
- **依存関係**：`requirements.txt`で`pytest>=7.0,<9.0`を指定（pytest-split v0.11.0はpytest <10が必要）；その他パッケージは通常どおりインストール
- **キャッシュ**：`requirements.txt`のチェックサムで依存関係をキャッシュ；pip パッケージとvirtualenvの両方をキャッシュして再インストール時間を短縮
- **MySQLセットアップ**：マイグレーション実行前にMySQLサービスが準備完了するまで最大30秒待機；CircleCIのサービスコンテナ初期化に時間がかかるため必要
- **マイグレーション**：テスト前に`python manage.py migrate`を実行してDBスキーマを最新に保つ
- **カバレッジ**：`pytest-cov`でコードカバレッジを計測し`coverage.xml`アーティファクトを生成
- **テスト結果**：JUnit XML結果をCircleCIのテスト可視化用に保存
- **リソース**：コスト効率のため`small`リソースクラスを使用
- **環境**：`CI=true`でSQLiteモード；`DJANGO_SETTINGS_MODULE`で正しいDjango設定を確保

**テスト**：pytest + pytest-djangoを使用。設定は`pytest.ini`（`DJANGO_SETTINGS_MODULE`を設定）。共通フィクスチャ（ユーザー、権限、店舗、倉庫）はプロジェクトルートの`conftest.py`に定義。各`Authority`フィクスチャはロール定数（`AUTHORITY_ADMIN=1`、`AUTHORITY_SHOP=2`、`AUTHORITY_WAREHOUSE=3`）に一致する明示的な`id`で作成し、テスト中のビューとフォームの権限ロジックが正しく動作するようにする。

アプリごとのテストファイル：
- `accounts/tests.py` — ログイン、ユーザーCRUD（管理者）、ユーザー管理
- `dashboard/tests.py` — 全3権限のDashboardView（管理者サマリー件数、店舗ランキング、倉庫在庫/注文件数）；発注ランキングのサービス層テスト（`get_monthly_order_summary`、`get_order_ranking`）
- `inventory/tests/test_goods_category.py` — GoodsCategoryの一覧/作成/更新/削除（`next`パラメータリダイレクトと`category_created` URL含む）
- `inventory/tests/test_goods.py` — 商品の一覧/作成/更新/削除（`category_created` GETパラメータの初期値と`can_delete`コンテキスト含む）。**商品削除テスト**：在庫ゼロの倉庫/店舗は削除可、OrderGoodsがある場合は削除不可
- `inventory/tests/test_warehouse.py` — 倉庫マスタCRUD、倉庫在庫一覧/編集、受注一覧/ステータス更新/CSV/PDFエクスポート
- `inventory/tests/test_shop.py` — 店舗マスタCRUD、店舗在庫一覧/編集、店舗削除
- `inventory/tests/test_order.py` — 発注商品一覧、発注作成、CSVダウンロード/インポート、発注履歴、CSV/PDFエクスポート（店舗側）
- `inventory/tests/test_relation.py` — 連携一覧/作成/削除、店舗連携倉庫一覧
- `inquiry/tests.py` — 問い合わせ一覧（受信/送信、ゲスト権限フィルター含む各種フィルター）、問い合わせ作成（認証チェック、バリデーション、カテゴリ選択）、ゲスト問い合わせ、詳細/ステータス更新、削除、label_from_instance、relationクエリパラメータ事前入力、**InquiryCategory CRUD**（一覧/作成/更新/削除の管理者専用ビュー、重複名バリデーション、関連レコードチェック、論理削除、問い合わせ一覧のカテゴリフィルター）、**ゲスト問い合わせフィルターテスト**（authority=guestでゲスト問い合わせのみ表示）、合計66テスト
- `common/tests.py` — 店舗名オートコンプリート（`TestShopNameAutocomplete`）と倉庫名オートコンプリート（`TestWarehouseNameAutocomplete`）のAPIテスト：部分一致、空クエリで全件返却、一致なしで空返却、論理削除済みレコード除外、レスポンス形式（`id`/`name`）の確認

**定期バッチ処理：**

- **月次注文サマリー更新バッチ** (`update_monthly_order_summary` managementコマンド) — 店舗/商品ごとの日次注文データを`MonthlyOrderSummary`レコードに集計してレポートと分析に使用。

**実装詳細：**

- **Managementコマンド** (`dashboard/management/commands/update_monthly_order_summary.py`)：
  - `order_filter_by_date_and_status()`で当日作成の注文をクエリ
  - (店舗, 商品)ごとにグループ化して`OrderGoods.quantity`の合計を集計
  - 再実行時の重複防止のため当日のレコードを削除（`MonthlyOrderSummary.objects.filter(count_date=today).delete()`）
  - `atomic()`トランザクションで原子性を保証
  - 1回のデータベース操作で`MonthlyOrderSummary`レコードをバルク作成

- **Cronスケジューリング：**
  - **Docker設定**：`/etc/cron.d/app-cron`にシステムレベルのcrontab（Dockerfileでデプロイ）
  - **crontabの環境変数**：
    ```
    TZ=Asia/Tokyo          # タイムスタンプログ用タイムゾーン
    PYTHONPATH=/app        # Pythonモジュールパス
    DJANGO_SETTINGS_MODULE=config.settings
    ```
  - **スケジュール設定**：
    - **開発環境**（現在）：`0 * * * *` — 毎時0分に実行（テスト用）
    - **本番環境**：`0 23 * * *` — 毎日23時に実行（デプロイ時に変更）
  - **実行**：Bashスクリプトがログ付きでDjangoコマンドをラップ：`bash /app/batch/run_monthly_order_summary.sh`
  - **ログ出力**：`>> /var/log/cron.log 2>&1` — stdoutとstderrの両方を`/var/log/cron.log`に記録

- **Bashスクリプト** (`batch/run_monthly_order_summary.sh`)：
  - ファイル冒頭で環境変数をエクスポート（Unix標準）
  - コマンド失敗時に即終了する`set -e`を使用
  - JSTタイムゾーンでバッチ開始・終了時刻をログ出力
  - 終了ログをcronログファイルで監視可能

- **Docker/Compose設定**：
  - **Dockerfile**：
    - タイムスタンプ一貫性のため`ENV TZ=Asia/Tokyo`
    - `COPY batch/crontab /etc/cron.d/app-cron`でcrontabをイメージに組み込み
    - `RUN chmod 0644 /etc/cron.d/app-cron`でcronデーモンが読み取れるよう権限設定
  - **docker-compose.yml**（cronサービス）：
    - コンテナ継続稼働に必要な`command: cron -f`でcronをフォアグラウンド実行
    - 冗長性のため環境変数に`TZ=Asia/Tokyo`
    - データベース準備完了を保証するため`db`サービスに依存

- **テスト** (`dashboard/tests.py::TestUpdateMonthlyOrderSummary`)：
  - `test_command_executes_successfully()` — コマンドがエラーなく実行されることを確認
  - `test_creates_monthly_summary_records()` — `MonthlyOrderSummary`レコードが作成されることを確認
  - `test_no_duplicate_records_on_multiple_executions()` — 削除ロジックで重複が防止されることを確認
  - `test_summary_data_accuracy()` — 集計された`total_quantity`が正確なことを確認

**デプロイ注意事項：**

- **本番スケジュールの変更**：`batch/crontab` 6行目を`0 * * * *`（毎時）から`0 23 * * *`（23時日次）に変更
- **crontabの変更はリビルドが必要**：crontabはDockerfileに組み込まれているため、スケジュール変更には`docker-compose down && docker-compose up -d --build`が必要
- **ログの監視**：`docker-compose exec cron tail -f /var/log/cron.log`
- **手動テスト実行**：`docker-compose exec cron bash /app/batch/run_monthly_order_summary.sh`
