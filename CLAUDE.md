# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Environment

This project uses Docker Compose with MySQL. Start the full stack with:

```bash
docker-compose up
```

The web server runs on `http://localhost:8000`. The MySQL database is exposed on port 3307 (mapped from container port 3306).

For local development without Docker (CI mode uses SQLite):

```bash
pip install -r requirements.txt
CI=true python manage.py migrate
CI=true python manage.py runserver
```

## Common Commands

```bash
# Run all tests (inside Docker container)
docker exec -e CI=true python_stock_app-web-1 pytest

# Run all tests (without Docker, uses SQLite)
CI=true pytest

# Run tests for a single app
CI=true pytest accounts/

# Run a single test class or method
CI=true pytest accounts/tests.py::TestLogin
CI=true pytest accounts/tests.py::TestLogin::test_login_success

# Apply migrations
python manage.py migrate

# Create a superuser (requires Authority id=1 to exist in DB)
python manage.py createsuperuser
```

## Architecture Overview

This is a Django inventory/stock management system for a multi-location retail business. It manages relationships between warehouses and shops, stock levels, orders, and user accounts.

**Apps:**

- `inventory` — Core domain models: `Warehouse`, `Shop`, `Goods`, `GoodsCategory`, `ShopStock`, `WarehouseStock`, `Relation` (warehouse↔shop link), `Order`, `OrderGoods`
- `accounts` — Custom user model extending `AbstractUser`, with `Authority` (role) and FK links to `Warehouse`/`Shop`
- `dashboard` — Home page view; `MonthlyOrderSummary` aggregation model
- `inquiry` — Inquiry/support ticket model between user roles
- `common` — Shared utilities: `BaseModel`, `ActiveManager`, role-check mixins, constants, context processor

**Ordering flow (shop staff):**

1. **発注商品選択画面** (`order_goods_list`, `OrderGoodsListView`) — Shop staff selects a product to order. Lists all active goods annotated with total stock across related warehouses. Supports category filter.
2. **発注画面** (`order_create/<goods_pk>/`, `OrderCreateView`) — Shop staff inputs per-warehouse order quantities. On POST, creates one `Order` per warehouse where `quantity > 0`, each with a linked `OrderGoods` record.
3. **CSV一括発注ダウンロード** (`order_csv_download`, `OrderCsvDownloadView`) — Downloads a CSV template pre-filled with related-warehouse stock data (columns: 倉庫ID, 倉庫名, カテゴリ, 商品ID, 商品名, 現在の在庫数, 発注数). The 発注数 column is left blank.
4. **CSV一括発注インポート** (`order_csv_import`, `OrderCsvImportView`) — Accepts the filled-in CSV via POST. Rows with blank or zero 発注数 are skipped. Multiple goods for the same warehouse are grouped under a single `Order` (one `Order` per warehouse per import).

**Shop staff order history flow:**

5. **発注履歴画面** (`order_history`, `OrderHistoryView`) — Shop staff views their own order history, grouped per order with related goods. Supports filtering by date range and status. Uses `services.get_order_history_data(shop)` and `services.build_rows(orders)` for shared query/row logic.
6. **発注履歴CSVエクスポート** (`order_history_csv_export`, `OrderHistoryCSVExportView`) — Downloads order history as CSV with date/status filter applied. Columns: 発注先倉庫, 商品名, 発注個数, ステータス, 発注日時, 更新日時. BOM is written manually with `response.write('﻿')` using `charset=utf-8`; do NOT use `charset=utf-8-sig`.
7. **発注履歴PDFエクスポート** (`order_history_pdf_export`, `OrderHistoryPDFExportView`) — Downloads order history as PDF using reportlab with the HeiseiKakuGo-W5 Japanese font.

**Shop staff stock management flow:**

- **店舗在庫一覧** (`shop_stock_list`, `ShopStockListView`) — Shop staff views all active goods with their store's current stock level. Stock is annotated via `Coalesce(Sum(...), 0)` so goods with no `ShopStock` record show 0. Supports category filter.
- **店舗在庫編集** (`shop_stock_edit/<goods_pk>/`, `ShopStockEditView`) — Shop staff updates the stock count for a specific goods item. Uses `ShopStock.objects.update_or_create()` so both new creation and updates are handled through the same POST. Returns 404 for unknown `goods_pk`.

**Master data management (admin only):**

- **GoodsCategory CRUD** (`goods_category_list/create/<pk>/edit/<pk>/delete/`) — Admin manages product categories. `GoodsCategoryCreateView.form_invalid()` handles `next` param redirect (used when creating from the goods form). `get_success_url()` appends `?category_created=<pk>` to `next` so the goods form can pre-select the new category.
- **Goods CRUD** (`goods_list/create/<pk>/edit/<pk>/delete/`) — Admin manages products. `GoodsCreateView` / `GoodsUpdateView` read `?category_created=<pk>` from GET params via `get_initial()` to pre-fill the category field after creating a new category inline. On `GoodsCreateView.form_valid()`, **automatic initial stock records are created**: `WarehouseStock` and `ShopStock` records with `stock=0` are created for all active warehouses and shops via `services.insert_initial_warehouse_stock_for_goods()` and `services.insert_initial_shop_stock_for_goods()`. This uses `transaction.atomic()` + `select_for_update()` for consistency, and `get_or_create()` with unique constraints to prevent duplicates if concurrent creates occur.
- **Warehouse CRUD** (`warehouses/`, `warehouses/create/`, `warehouses/<pk>/edit/`, `warehouses/<pk>/delete/`) — Admin manages warehouses. `WarehouseUpdateView` exposes `can_delete` context (False if warehouse has linked users, stock, or relations).
- **Shop CRUD** (`shops/`, `shops/create/`, `shops/<pk>/edit/`, `shops/<pk>/delete/`) — Admin manages shops. `ShopUpdateView` exposes `can_delete` context (False if shop has linked users, stock, relations, or monthly summaries).
- **Relation CRUD** (`relations/`, `relations/create/`, `relations/<pk>/delete/`) — Admin manages warehouse↔shop links. `RelationForm.clean()` prevents duplicate active relations for the same shop–warehouse pair.

**Warehouse staff order management flow:**

- **受注管理一覧** (`warehouse_orders/`, `WarehouseOrderListView`) — Warehouse staff views orders received for their warehouse. Supports filtering by date range and status. Uses module-level helpers `_get_filtered_orders()` and `_build_rows()`.
- **受注ステータス更新** (`warehouse_orders/<pk>/status/`, `WarehouseOrderStatusUpdateView`) — Warehouse staff updates order status. Only `ORDERED(0)` and `PREPARING(1)` are accepted (`ALLOWED_STATUSES`); other values return an error. Returns 404 for orders not belonging to the logged-in warehouse.
- **受注CSVエクスポート** (`warehouse_orders/export/csv/`, `WarehouseOrderCSVExportView`) — Downloads received orders as CSV. Uses `content_type='text/csv; charset=utf-8-sig'` (note: Django encodes each `write()` call with utf-8-sig, adding BOM to every row). Columns: 発注元店舗, 商品名, 発注個数, ステータス, 発注日時, 更新日時.
- **受注PDFエクスポート** (`warehouse_orders/export/pdf/`, `WarehouseOrderPDFExportView`) — Downloads received orders as PDF using reportlab.

**Shop connected-warehouse list:**

- **連携倉庫一覧** (`shop/connected-warehouses/`, `ShopConnectedWarehouseListView`) — Shop staff views warehouses linked to their store. Used as an entry point to create inquiries via `?relation=<id>`.

**Inquiry flow:**

- **問い合わせ一覧** (`inquiry_list`, `InquiryListView`) — Shows received and sent inquiries. Received list is filtered to the logged-in user's authority + belonging (shop or warehouse). Admin sees all inquiries sent to admin authority; shop/warehouse staff see only those addressed to their specific location via `to_relation`. Supports filter by authority, shop, warehouse, and status.
- **問い合わせ送信** (`inquiry_create`, `InquiryCreateView`) — For logged-in non-admin users. The `to_relation` field shows only relations linked to the user's shop/warehouse; `label_from_instance` is used to display only the counterpart name (warehouse name for shop staff, shop name for warehouse staff). Accepts a `?relation=<id>` query parameter (e.g. from the connected-warehouse list page) to pre-populate `to_authority` and `to_relation`.
- **ゲスト問い合わせ** (`inquiry_create_guest`, `InquiryGuestCreateView`) — For unauthenticated users; always sent to the admin authority.
- **問い合わせ詳細・ステータス更新** (`inquiry_detail/<pk>/`, `InquiryDetailView`) — Receiver can update status (未対応/対応中/対応済み); sender can view only.
- **論理削除** (`inquiry_delete/<pk>/`, `InquiryDeleteView`) — Sender or receiver can soft-delete (`delete_flg=True`).

**Key patterns:**

- **Soft delete**: All models inherit from `BaseModel` which has `delete_flg`. Use `Model.active_objects` (filters `delete_flg=False`) for normal queries; `Model.objects` gives all records including deleted.
- **Role-based access**: Three roles defined in `common/constants.py` — `AUTHORITY_ADMIN=1`, `AUTHORITY_SHOP=2`, `AUTHORITY_WAREHOUSE=3`. Access control uses mixins in `common/mixins.py` (`AdminRequiredMixin`, `ShopStaffRequiredMixin`, `WarehouseStaffRequiredMixin`). Constants are injected into every template via the `authority_constants` context processor.
- **User constraints**: Shop staff (`authority_id=2`) must have a `shop` FK; warehouse staff (`authority_id=3`) must have a `warehouse` FK. This is enforced in `User.clean()`.
- **Cross-app FK references**: `accounts.User` references `inventory.Warehouse` and `inventory.Shop` by string (`'inventory.Warehouse'`). `dashboard.MonthlyOrderSummary` references `inventory` models similarly. Avoid circular imports by using string-form FK targets.
- **services.py**: Shared business logic that is used by multiple views lives in `<app>/services.py`. Views handle only HTTP (request parsing, rendering, redirect); services contain queryset building, filtering, and data transformation. Example: `inventory/services.py` contains `get_order_history_data()`, `order_filter_by_date_and_status()`, `build_rows()`, `get_shop_stock_list()`, `update_or_create_shop_stock()` etc. CSV exports write BOM manually with `response.write('﻿')` using `charset=utf-8` (NOT `charset=utf-8-sig`, which would insert a BOM on every `write()` call and corrupt the file).
- **label_from_instance**: Use `field.label_from_instance = lambda obj: ...` on a `ModelChoiceField` to customise the display text of each choice without subclassing the field. Set this after assigning `queryset`.
- **Form pre-population via query param**: Pass data from a list page to a create form by appending a query parameter to the URL (e.g. `?relation=<id>`). The view reads `request.GET.get('relation')` and passes it to the form's `__init__`; the form sets `self.initial[field]` to pre-fill specific fields.
- **update_or_create for upsert**: Use `Model.objects.update_or_create(lookup_fields, defaults={...})` when a POST should create a new record or update an existing one transparently (e.g. `ShopStockEditView`).

**Frontend styling:**

- **Bootstrap first**: Use Bootstrap utility classes and components wherever possible.
- **Custom CSS**: If Bootstrap cannot cover the requirement (e.g. gradients, specific `rgba` colors, `letter-spacing`, hover transitions), write the CSS in an external `.css` file — never inline `style=""` attributes on HTML elements, and never `<style>` blocks inside templates.
- **CSS file locations**: Place app-specific CSS under `<app>/static/<app>/css/`. Shared CSS goes in `common/static/common/css/common.css`. Load files via `{% load static %}` and `<link rel="stylesheet" href="{% static '...' %}">`.
- **STATIC_URL**: Must be set to `'/static/'` (with leading slash) in `settings.py` so that `{% static %}` generates absolute paths that resolve correctly on all pages regardless of URL depth.
- **Page-specific CSS**: Use `{% block extra_css %}` in templates that extend `base.html` to load page-specific CSS files:
  ```html
  {% load static %}
  {% block extra_css %}
  <link rel="stylesheet" href="{% static 'app/css/app.css' %}">
  {% endblock %}
  ```

**URL conventions:**

- **Plural resource names**: Collections use plural form — `warehouses/`, `shops/`, `orders/`, etc.
- **Hyphens in URL paths**: Multi-word segments use hyphens — `status-update`, `connected-warehouses`.
- **Underscores in `name=`**: The `name=` parameter follows Python identifier convention — `warehouse_order_status_update`.
- **Static paths before variable paths**: Within the same resource group, place static paths (e.g. `warehouses/stock/`) before variable paths (e.g. `warehouses/<int:pk>/edit/`) for readability.
- **Standard CRUD pattern**:
  ```
  <resource>/                 一覧
  <resource>/create/          作成
  <resource>/<pk>/edit/       編集
  <resource>/<pk>/delete/     削除
  ```

**Database:** MySQL in Docker (`stockdb`). CI uses SQLite (controlled by the `CI` environment variable in `config/settings.py`).

**CI:** CircleCI runs migrations and `pytest` on every push.

**CircleCI Configuration** (`.circleci/config.yml`):
- **Parallelism**: 4 containers run tests in parallel for faster feedback
- **Test Distribution**: `pytest-split` automatically divides tests by past execution timings for balanced parallel execution (`.circleci/.test_durations` stores timing data across runs)
- **Caching**: Dependencies cached by `requirements.txt` checksum; pip packages and virtualenv both cached to reduce reinstall time
- **Coverage**: `pytest-cov` measures code coverage and generates `coverage.xml` artifact for CI dashboard tracking
- **Test Results**: JUnit XML results stored for CircleCI test visualization
- **Resource**: `small` resource class for cost efficiency
- **Environment**: `CI=true` sets SQLite mode; `DJANGO_SETTINGS_MODULE` ensures correct Django config

**Testing:** Uses pytest + pytest-django. Configuration is in `pytest.ini` (sets `DJANGO_SETTINGS_MODULE`). Shared fixtures (users, authorities, shops, warehouses) are defined in `conftest.py` at the project root. Each `Authority` fixture is created with an explicit `id` matching the role constants (`AUTHORITY_ADMIN=1`, `AUTHORITY_SHOP=2`, `AUTHORITY_WAREHOUSE=3`) so that permission logic in views and forms works correctly during tests.

Test files per app:
- `accounts/tests.py` — login, user CRUD (admin), user management
- `dashboard/tests.py` — DashboardView for all 3 roles (admin summary counts, shop rankings, warehouse stock/order counts)
- `inventory/tests/test_goods_category.py` — GoodsCategory list/create/update/delete (including `next` param redirect and `category_created` URL)
- `inventory/tests/test_goods.py` — Goods list/create/update/delete (including `category_created` GET param initial value and `can_delete` context)
- `inventory/tests/test_warehouse.py` — Warehouse master CRUD, warehouse stock list/edit, warehouse order list/status-update/CSV/PDF export
- `inventory/tests/test_shop.py` — Shop master CRUD, shop stock list/edit, shop delete
- `inventory/tests/test_order.py` — order goods list, order create, CSV download/import, order history, CSV/PDF export (shop side)
- `inventory/tests/test_relation.py` — relation list/create/delete, shop connected-warehouse list
- `inquiry/tests.py` — inquiry list (received/sent, filters), inquiry create (auth checks, validation), guest inquiry, detail/status update, delete, form label_from_instance, relation query-param pre-population
