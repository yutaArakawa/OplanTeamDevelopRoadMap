# Django コーディングパターン

## 主要パターン

- **論理削除**：全モデルは`delete_flg`を持つ`BaseModel`を継承。通常のクエリは`Model.active_objects`（`delete_flg=False`でフィルター）；`Model.objects`は削除済みを含む全レコードを返す。

- **ロールベースアクセス制御**：`common/constants.py`で3つのロールを定義 — `AUTHORITY_ADMIN=1`、`AUTHORITY_SHOP=2`、`AUTHORITY_WAREHOUSE=3`。アクセス制御は`common/mixins.py`のMixin（`AdminRequiredMixin`、`ShopStaffRequiredMixin`、`WarehouseStaffRequiredMixin`）を使用。定数は`authority_constants`コンテキストプロセッサで全テンプレートに注入。

- **ユーザー制約**：店舗スタッフ（`authority_id=2`）は`shop` FKが必須；倉庫スタッフ（`authority_id=3`）は`warehouse` FKが必須。`User.clean()`で強制。

- **アプリ間FK参照**：`accounts.User`は`inventory.Warehouse`と`inventory.Shop`を文字列（`'inventory.Warehouse'`）で参照。`dashboard.MonthlyOrderSummary`も同様。循環インポートを避けるため文字列形式のFKターゲットを使用。

- **services.py**：複数ビューで共有するビジネスロジックは`<app>/services.py`に配置。ビューはHTTPのみ担当（リクエスト解析、レンダリング、リダイレクト）；サービスはクエリセット構築、フィルタリング、データ変換を担当。例：`inventory/services.py`には`get_order_history_data()`、`order_filter_by_date_and_status()`、`build_rows()`、`get_shop_stock_list()`、`update_or_create_shop_stock()`など；`dashboard/services.py`には`get_monthly_order_summary(date, shop=None)`と`get_order_ranking(summary_queryset, limit=10)`。

- **CSVエクスポートのBOM**：BOMは`charset=utf-8`で`response.write('﻿')`を使って手動書き込み（`charset=utf-8-sig`はwrite()のたびにBOMが挿入されてファイルが破損するため使用禁止）。

- **label_from_instance**：`ModelChoiceField`の`field.label_from_instance = lambda obj: ...`でフィールドをサブクラス化せずに各選択肢の表示テキストをカスタマイズ。`queryset`代入後に設定すること。

- **クエリパラメータによるフォーム事前入力**：URLにクエリパラメータを付加して一覧画面から作成フォームにデータを渡す（例：`?relation=<id>`）。ビューで`request.GET.get('relation')`を読み取りフォームの`__init__`に渡す；フォームは`self.initial[field]`で特定フィールドを事前入力。

- **update_or_create によるアップサート**：POSTで新規作成と既存レコード更新を透過的に処理する場合は`Model.objects.update_or_create(lookup_fields, defaults={...})`を使用（例：`ShopStockEditView`）。

- **ゲストエンティティ処理**：ゲスト/未認証の送信を表すモデルは`from_user=NULL`と`from_authority=NULL`でゲストレコードを識別。両ForeignKeyフィールドがNULLの場合に人間が読めるラベル（「ゲスト」）を返す`get_*_display()`メソッドを提供。ビューとテンプレートは特別なクエリ値（例：`authority=guest`）でフィルター可能；ビューは`filter(from_user__isnull=True, from_authority__isnull=True)`に変換。

---

## フロントエンドスタイリング（Djangoテンプレート）

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

---

## URL規則

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
