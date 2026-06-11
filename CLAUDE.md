# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Environment

This project uses Docker Compose with MySQL. There are two Docker Compose files:

- `docker-compose.dev.yml` — Development: Django `runserver` directly on port 8000
- `docker-compose.prod.yml` — Production: nginx (port 9149) → Gunicorn → Django

**Development (local):**
```bash
docker-compose -f docker-compose.dev.yml up
```
The web server runs on `http://localhost:8000`. The MySQL database is exposed on port 3307 (mapped from container port 3306).

**Production:**
```bash
docker-compose -f docker-compose.prod.yml up -d --build
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```
The web server runs on `http://localhost:9149` via nginx. `collectstatic` must be run after build whenever static files (CSS/JS) change.

For local development without Docker (CI mode uses SQLite):

```bash
pip install -r requirements.txt
CI=true python manage.py migrate
CI=true python manage.py runserver
```

## Common Commands

```bash
# Run all tests (faster — uses SQLite without Docker)
CI=true pytest

# Run all tests (inside Docker dev container)
docker exec -e CI=true python_stock_app-web-1 pytest

# Run tests for a single app
CI=true pytest accounts/

# Run a single test class or method
CI=true pytest accounts/tests.py::TestLogin
CI=true pytest accounts/tests.py::TestLogin::test_login_success

# Apply migrations
python manage.py migrate

# Collect static files (required for production)
python manage.py collectstatic --noinput

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

**Dashboard (home page):**

- **Admin**: Summary counts (warehouses, shops, goods, categories, users, pending orders)
- **Shop staff**: 
  - **自店舗 発注ランキング** — Top 10 products ordered by this shop on previous day, aggregated from `MonthlyOrderSummary` via `services.get_monthly_order_summary()` and `services.get_order_ranking()`
  - **全店舗 発注ランキング** — Top 10 products ordered across all shops on previous day
- **Warehouse staff**: Stock counts (own warehouse inventory count, new/preparing order counts) and warehouse stock list

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
- **Goods CRUD** (`goods_list/create/<pk>/edit/<pk>/delete/`) — Admin manages products. `GoodsCreateView` / `GoodsUpdateView` read `?category_created=<pk>` from GET params via `get_initial()` to pre-fill the category field after creating a new category inline. On `GoodsCreateView.form_valid()`, **automatic initial stock records are created**: `WarehouseStock` and `ShopStock` records with `stock=0` are created for all active warehouses and shops via `services.insert_initial_warehouse_stock_for_goods()` and `services.insert_initial_shop_stock_for_goods()`. This uses `transaction.atomic()` + `select_for_update()` for consistency, and `get_or_create()` with unique constraints to prevent duplicates if concurrent creates occur. **Goods deletion**: `Goods.has_related_records()` checks for related stock records with `stock__gt=0` (not merely existence), and `OrderGoods` existence. This allows deletion of newly created goods with zero stock immediately after creation.
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

- **問い合わせ一覧** (`inquiry_list`, `InquiryListView`) — Shows received and sent inquiries. Received list is filtered to the logged-in user's authority + belonging (shop or warehouse). Admin sees all inquiries sent to admin authority; shop/warehouse staff see only those addressed to their specific location via `to_relation`. Supports filtering by authority (including guest queries via `authority=guest`), shop, warehouse, and status. **Guest inquiries** (`from_user=NULL` and `from_authority=NULL`) are identified and displayed as "ゲスト" via `Inquiry.get_from_authority_display()`.
- **問い合わせ送信** (`inquiry_create`, `InquiryCreateView`) — For logged-in non-admin users. The `to_relation` field shows only relations linked to the user's shop/warehouse; `label_from_instance` is used to display only the counterpart name (warehouse name for shop staff, shop name for warehouse staff). Accepts a `?relation=<id>` query parameter (e.g. from the connected-warehouse list page) to pre-populate `to_authority` and `to_relation`.
- **ゲスト問い合わせ** (`inquiry_create_guest`, `InquiryGuestCreateView`) — For unauthenticated users; always sent to the admin authority.
- **問い合わせ詳細・ステータス更新** (`inquiry_detail/<pk>/`, `InquiryDetailView`) — Receiver can update status (未対応/対応中/対応済み); sender can view only.
- **論理削除** (`inquiry_delete/<pk>/`, `InquiryDeleteView`) — Sender or receiver can soft-delete (`delete_flg=True`).

**Inquiry category management (admin only):**

- **InquiryCategory model** — Categorizes inquiries for better organization. Inherits from `BaseModel` for soft-delete support. Enforces unique category names (case-sensitive, only among non-deleted records) via `UniqueConstraint` with `condition=Q(delete_flg=False)` and model-level `clean()` validation. Provides `has_related_records()` method to check if category is linked to any inquiries before deletion.
- **カテゴリ一覧** (`categories/`, `inquiry_category_list`, `InquiryCategoryListView`) — Admin-only view listing all active inquiry categories. Ordered by name.
- **カテゴリ作成** (`categories/create/`, `inquiry_category_create`, `InquiryCategoryCreateView`) — Admin creates new categories. Supports inline creation via `next` parameter (similar to GoodsCategory pattern): form submission with `next=<url>` pre-filled appends `?category_created=<pk>` to redirect URL, allowing parent forms (e.g. inquiry creation) to pre-select newly created categories.
- **カテゴリ編集** (`categories/<pk>/edit/`, `inquiry_category_edit`, `InquiryCategoryUpdateView`) — Admin updates category name. Template displays `can_delete` context flag (False if category has linked inquiries).
- **カテゴリ削除** (`categories/<pk>/delete/`, `inquiry_category_delete`, `InquiryCategoryDeleteView`) — Admin soft-deletes categories. Checks `has_related_records()` before deletion; if related inquiries exist, shows error message and redirects without deleting.
- **カテゴリ選択（問い合わせ作成時）** — Both `InquiryCreateView` and `InquiryGuestCreateView` include `inquiry_category` as a required field. Users must select a category when creating an inquiry. Form renders category field as `form-select` (Bootstrap).
- **カテゴリフィルター（問い合わせ一覧）** — `InquiryListView` supports filtering both received and sent inquiries by category via `?category=<id>` query parameter. Passes all active categories to template context as `categories` for filter UI.

**Key patterns:**

- **Soft delete**: All models inherit from `BaseModel` which has `delete_flg`. Use `Model.active_objects` (filters `delete_flg=False`) for normal queries; `Model.objects` gives all records including deleted.
- **Role-based access**: Three roles defined in `common/constants.py` — `AUTHORITY_ADMIN=1`, `AUTHORITY_SHOP=2`, `AUTHORITY_WAREHOUSE=3`. Access control uses mixins in `common/mixins.py` (`AdminRequiredMixin`, `ShopStaffRequiredMixin`, `WarehouseStaffRequiredMixin`). Constants are injected into every template via the `authority_constants` context processor.
- **User constraints**: Shop staff (`authority_id=2`) must have a `shop` FK; warehouse staff (`authority_id=3`) must have a `warehouse` FK. This is enforced in `User.clean()`.
- **Cross-app FK references**: `accounts.User` references `inventory.Warehouse` and `inventory.Shop` by string (`'inventory.Warehouse'`). `dashboard.MonthlyOrderSummary` references `inventory` models similarly. Avoid circular imports by using string-form FK targets.
- **services.py**: Shared business logic that is used by multiple views lives in `<app>/services.py`. Views handle only HTTP (request parsing, rendering, redirect); services contain queryset building, filtering, and data transformation. Example: `inventory/services.py` contains `get_order_history_data()`, `order_filter_by_date_and_status()`, `build_rows()`, `get_shop_stock_list()`, `update_or_create_shop_stock()` etc.; `dashboard/services.py` contains `get_monthly_order_summary(date, shop=None)` (filters by date/shop and returns QuerySet) and `get_order_ranking(summary_queryset, limit=10)` (receives QuerySet, aggregates by goods, and returns ranked data in values format). CSV exports write BOM manually with `response.write('﻿')` using `charset=utf-8` (NOT `charset=utf-8-sig`, which would insert a BOM on every `write()` call and corrupt the file).
- **label_from_instance**: Use `field.label_from_instance = lambda obj: ...` on a `ModelChoiceField` to customise the display text of each choice without subclassing the field. Set this after assigning `queryset`.
- **Form pre-population via query param**: Pass data from a list page to a create form by appending a query parameter to the URL (e.g. `?relation=<id>`). The view reads `request.GET.get('relation')` and passes it to the form's `__init__`; the form sets `self.initial[field]` to pre-fill specific fields.
- **update_or_create for upsert**: Use `Model.objects.update_or_create(lookup_fields, defaults={...})` when a POST should create a new record or update an existing one transparently (e.g. `ShopStockEditView`).
- **Guest entity handling**: For models representing guest/unauthenticated submissions (e.g. `Inquiry` from `InquiryGuestCreateView`), use `from_user=NULL` and `from_authority=NULL` to identify guest records. Provide a `get_*_display()` method (e.g. `get_from_authority_display()`) to return a human-readable label ("ゲスト") when both ForeignKey fields are NULL. Views and templates can filter via special query values (e.g. `authority=guest`) which the view translates to `filter(from_user__isnull=True, from_authority__isnull=True)`.

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
- **Test Distribution**: `pytest-split` v0.11.0 automatically divides tests by past execution timings for balanced parallel execution. Uses options: `--splits=4 --group=$((CIRCLE_NODE_INDEX + 1)) --splitting-algorithm=least_duration --durations-path=.circleci/.test_durations --store-durations`. First run distributes tests evenly (no timing data); subsequent runs use `.circleci/.test_durations` for optimal distribution.
- **Dependencies**: `requirements.txt` specifies `pytest>=7.0,<9.0` (pytest-split v0.11.0 requires pytest <10); other packages installed normally
- **Caching**: Dependencies cached by `requirements.txt` checksum; pip packages and virtualenv both cached to reduce reinstall time
- **MySQL Setup**: Waits up to 30 seconds for MySQL service to be ready before running migrations; required because CircleCI service container initialization takes time
- **Migrations**: Runs `python manage.py migrate` before tests to ensure DB schema is current
- **Coverage**: `pytest-cov` measures code coverage and generates `coverage.xml` artifact for CI dashboard tracking
- **Test Results**: JUnit XML results stored for CircleCI test visualization
- **Resource**: `small` resource class for cost efficiency
- **Environment**: `CI=true` sets SQLite mode; `DJANGO_SETTINGS_MODULE` ensures correct Django config

**Testing:** Uses pytest + pytest-django. Configuration is in `pytest.ini` (sets `DJANGO_SETTINGS_MODULE`). Shared fixtures (users, authorities, shops, warehouses) are defined in `conftest.py` at the project root. Each `Authority` fixture is created with an explicit `id` matching the role constants (`AUTHORITY_ADMIN=1`, `AUTHORITY_SHOP=2`, `AUTHORITY_WAREHOUSE=3`) so that permission logic in views and forms works correctly during tests.

Test files per app:
- `accounts/tests.py` — login, user CRUD (admin), user management
- `dashboard/tests.py` — DashboardView for all 3 roles (admin summary counts, shop rankings, warehouse stock/order counts); Service layer tests for order ranking (`get_monthly_order_summary`, `get_order_ranking`)
- `inventory/tests/test_goods_category.py` — GoodsCategory list/create/update/delete (including `next` param redirect and `category_created` URL)
- `inventory/tests/test_goods.py` — Goods list/create/update/delete (including `category_created` GET param initial value and `can_delete` context). **Goods deletion tests**: zero-stock warehouse/shop deletion allowed, OrderGoods blocks deletion
- `inventory/tests/test_warehouse.py` — Warehouse master CRUD, warehouse stock list/edit, warehouse order list/status-update/CSV/PDF export
- `inventory/tests/test_shop.py` — Shop master CRUD, shop stock list/edit, shop delete
- `inventory/tests/test_order.py` — order goods list, order create, CSV download/import, order history, CSV/PDF export (shop side)
- `inventory/tests/test_relation.py` — relation list/create/delete, shop connected-warehouse list
- `inquiry/tests.py` — inquiry list (received/sent, filters including guest authority filter), inquiry create (auth checks, validation, category selection), guest inquiry, detail/status update, delete, form label_from_instance, relation query-param pre-population, **InquiryCategory CRUD** (list/create/update/delete admin-only views, duplicate name validation, related records check, soft delete, category filter in inquiry list), **guest inquiry filtering tests** (authority=guest shows only guest inquiries), total 66 tests

**Scheduled batch jobs:**

- **月次注文サマリー更新バッチ** (`update_monthly_order_summary` management command) — Aggregates daily order data per shop/goods into `MonthlyOrderSummary` records for reporting and analytics.

**Implementation details:**

- **Management command** (`dashboard/management/commands/update_monthly_order_summary.py`):
  - Queries orders created today via `order_filter_by_date_and_status()`
  - Groups orders by (shop, goods) to aggregate total `OrderGoods.quantity`
  - Deletes existing records for today (`MonthlyOrderSummary.objects.filter(count_date=today).delete()`) to prevent duplicates on re-execution
  - Uses `atomic()` transaction for atomicity
  - Bulk-creates `MonthlyOrderSummary` records in a single database operation

- **Cron scheduling:**
  - **Docker setup**: System-level crontab at `/etc/cron.d/app-cron` (deployed in `Dockerfile`)
  - **Environment variables** in crontab:
    ```
    TZ=Asia/Tokyo          # Timezone for timestamp logging
    PYTHONPATH=/app        # Python module path
    DJANGO_SETTINGS_MODULE=config.settings
    ```
  - **Schedule configuration**: 
    - **Development** (current): `0 * * * *` — Runs every hour at minute 0 (hourly testing)
    - **Production**: `0 23 * * *` — Runs daily at 23:00 (to be changed upon deployment)
  - **Execution**: Bash script wraps the Django command with logging: `bash /app/batch/run_monthly_order_summary.sh`
  - **Log output**: `>> /var/log/cron.log 2>&1` — Both stdout and stderr logged to `/var/log/cron.log`

- **Bash script** (`batch/run_monthly_order_summary.sh`):
  - Exports environment variables at file start (standard Unix practice)
  - Uses `set -e` to fail fast if any command fails
  - Logs batch start and end times with JST timezone
  - Exit logs visible in cron log file for monitoring

- **Docker/Compose configuration**:
  - **Dockerfile**: 
    - `ENV TZ=Asia/Tokyo` for timestamp consistency
    - `COPY batch/crontab /etc/cron.d/app-cron` to embed crontab in image
    - `RUN chmod 0644 /etc/cron.d/app-cron` to make it readable by cron daemon
  - **docker-compose.yml** (cron service):
    - `command: cron -f` to run cron in foreground (required for container uptime)
    - `TZ=Asia/Tokyo` environment variable for redundancy
    - Depends on `db` service to ensure database is ready

- **Testing** (`dashboard/tests.py::TestUpdateMonthlyOrderSummary`):
  - `test_command_executes_successfully()` — Verifies command runs without error
  - `test_creates_monthly_summary_records()` — Confirms `MonthlyOrderSummary` records are created
  - `test_no_duplicate_records_on_multiple_executions()` — Verifies deletion logic prevents duplicates
  - `test_summary_data_accuracy()` — Confirms aggregated `total_quantity` is correct

**Deployment notes:**

- **To change production schedule**: Edit `batch/crontab` line 6 from `0 * * * *` (hourly) to `0 23 * * *` (23:00 daily)
- **Crontab changes require rebuild**: Since crontab is embedded in Dockerfile, any schedule change requires `docker-compose down && docker-compose up -d --build`
- **Logs can be monitored via**: `docker-compose exec cron tail -f /var/log/cron.log`
- **Manual execution for testing**: `docker-compose exec cron bash /app/batch/run_monthly_order_summary.sh`
