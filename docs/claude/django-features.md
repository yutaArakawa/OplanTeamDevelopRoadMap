# Django 機能詳細

## ダッシュボード（ホーム画面）

- **管理者**：サマリー件数（倉庫、店舗、商品、カテゴリ、ユーザー、発注中の注文）
- **店舗スタッフ**：
  - **自店舗 発注ランキング** — 前日に自店舗が発注した商品トップ10。`MonthlyOrderSummary`から`services.get_monthly_order_summary()`と`services.get_order_ranking()`で集計
  - **全店舗 発注ランキング** — 前日に全店舗で発注された商品トップ10
- **倉庫スタッフ**：在庫件数（自倉庫の在庫数、新規/準備中の注文件数）と倉庫在庫一覧

## 発注フロー（店舗スタッフ）

1. **発注商品選択画面** (`order_goods_list`, `OrderGoodsListView`) — 店舗スタッフが発注する商品を選択。連携倉庫の在庫合計でアノテーションされた有効商品一覧を表示。カテゴリフィルター対応。
2. **発注画面** (`order_create/<goods_pk>/`, `OrderCreateView`) — 店舗スタッフが倉庫ごとの発注数を入力。POSTで`quantity > 0`の倉庫ごとに`Order`を1件作成し、紐づく`OrderGoods`レコードも作成。
3. **CSV一括発注ダウンロード** (`order_csv_download`, `OrderCsvDownloadView`) — 連携倉庫の在庫データを事前入力したCSVテンプレートをダウンロード（列：倉庫ID、倉庫名、カテゴリ、商品ID、商品名、現在の在庫数、発注数）。発注数列は空欄。
4. **CSV一括発注インポート** (`order_csv_import`, `OrderCsvImportView`) — 入力済みCSVをPOSTで受け付け。発注数が空または0の行はスキップ。同じ倉庫への複数商品は1件の`Order`にまとめる（インポートごとに倉庫1件につき`Order`1件）。

## 発注履歴フロー（店舗スタッフ）

5. **発注履歴画面** (`order_history`, `OrderHistoryView`) — 店舗スタッフが自店舗の発注履歴を閲覧。注文ごとに関連商品をまとめて表示。日付範囲とステータスでフィルター対応。共有クエリ/行ロジックに`services.get_order_history_data(shop)`と`services.build_rows(orders)`を使用。
6. **発注履歴CSVエクスポート** (`order_history_csv_export`, `OrderHistoryCSVExportView`) — 日付/ステータスフィルターを適用した発注履歴をCSVでダウンロード。列：発注先倉庫、商品名、発注個数、ステータス、発注日時、更新日時。BOMは`charset=utf-8`で`response.write('﻿')`を使って手動書き込み（`charset=utf-8-sig`はwrite()のたびにBOMが挿入されるため使用禁止）。
7. **発注履歴PDFエクスポート** (`order_history_pdf_export`, `OrderHistoryPDFExportView`) — reportlabとHeiseiKakuGo-W5日本語フォントを使って発注履歴をPDFでダウンロード。

## 店舗在庫管理フロー（店舗スタッフ）

- **店舗在庫一覧** (`shop_stock_list`, `ShopStockListView`) — 店舗スタッフが有効な全商品と自店舗の現在在庫数を閲覧。`ShopStock`レコードがない商品は`Coalesce(Sum(...), 0)`で0表示。カテゴリフィルター対応。
- **店舗在庫編集** (`shop_stock_edit/<goods_pk>/`, `ShopStockEditView`) — 特定商品の在庫数を更新。`ShopStock.objects.update_or_create()`を使用するため新規作成と更新の両方を同じPOSTで処理。不明な`goods_pk`は404を返す。

## マスタデータ管理（管理者のみ）

- **GoodsCategory CRUD** (`goods_category_list/create/<pk>/edit/<pk>/delete/`) — 管理者が商品カテゴリを管理。`GoodsCategoryCreateView.form_invalid()`が`next`パラメータのリダイレクトを処理（商品フォームからの作成時に使用）。`get_success_url()`が`next`に`?category_created=<pk>`を付加することで商品フォームが新カテゴリを事前選択できる。
- **Goods CRUD** (`goods_list/create/<pk>/edit/<pk>/delete/`) — 管理者が商品を管理。`GoodsCreateView`/`GoodsUpdateView`は`get_initial()`でGETパラメータから`?category_created=<pk>`を読み取り、インライン作成後のカテゴリフィールドを事前入力。`GoodsCreateView.form_valid()`では**初期在庫レコードが自動作成**される：`services.insert_initial_warehouse_stock_for_goods()`と`services.insert_initial_shop_stock_for_goods()`で全有効倉庫・店舗に`stock=0`の`WarehouseStock`/`ShopStock`レコードを作成。`transaction.atomic()` + `select_for_update()`で整合性を保ち、ユニーク制約付きの`get_or_create()`で同時作成時の重複を防止。**商品削除**：`Goods.has_related_records()`は`stock__gt=0`の在庫レコード（単なる存在ではなく）と`OrderGoods`の存在をチェック。これにより作成直後の在庫ゼロ商品の削除が可能。
- **Warehouse CRUD** (`warehouses/`, `warehouses/create/`, `warehouses/<pk>/edit/`, `warehouses/<pk>/delete/`) — 管理者が倉庫を管理。`WarehouseUpdateView`は`can_delete`コンテキストを提供（倉庫にユーザー・在庫・連携がある場合はFalse）。
- **Shop CRUD** (`shops/`, `shops/create/`, `shops/<pk>/edit/`, `shops/<pk>/delete/`) — 管理者が店舗を管理。`ShopUpdateView`は`can_delete`コンテキストを提供（店舗にユーザー・在庫・連携・月次サマリーがある場合はFalse）。
- **Relation CRUD** (`relations/`, `relations/create/`, `relations/<pk>/delete/`) — 管理者が倉庫↔店舗の連携を管理。`RelationForm.clean()`で同じ店舗・倉庫ペアの有効な重複連携を防止。

## 受注管理フロー（倉庫スタッフ）

- **受注管理一覧** (`warehouse_orders/`, `WarehouseOrderListView`) — 倉庫スタッフが自倉庫への受注を閲覧。日付範囲とステータスでフィルター対応。モジュールレベルのヘルパー`_get_filtered_orders()`と`_build_rows()`を使用。
- **受注ステータス更新** (`warehouse_orders/<pk>/status/`, `WarehouseOrderStatusUpdateView`) — 倉庫スタッフが受注ステータスを更新。`ORDERED(0)`と`PREPARING(1)`のみ受付（`ALLOWED_STATUSES`）；それ以外はエラーを返す。ログイン中の倉庫に属さない注文は404を返す。
- **受注CSVエクスポート** (`warehouse_orders/export/csv/`, `WarehouseOrderCSVExportView`) — 受注をCSVでダウンロード。`content_type='text/csv; charset=utf-8-sig'`を使用（DjangoはutF-8-sigで各`write()`呼び出しをエンコードし、全行にBOMを付加することに注意）。列：発注元店舗、商品名、発注個数、ステータス、発注日時、更新日時。
- **受注PDFエクスポート** (`warehouse_orders/export/pdf/`, `WarehouseOrderPDFExportView`) — reportlabを使って受注をPDFでダウンロード。

## 店舗の連携倉庫一覧

- **連携倉庫一覧** (`shop/connected-warehouses/`, `ShopConnectedWarehouseListView`) — 店舗スタッフが自店舗に連携された倉庫を閲覧。`?relation=<id>`で問い合わせ作成へのエントリーポイントとして使用。

## 問い合わせフロー

- **問い合わせ一覧** (`inquiry_list`, `InquiryListView`) — 受信・送信済みの問い合わせを表示。受信一覧はログインユーザーの権限と所属（店舗または倉庫）でフィルター。管理者は管理者権限宛の全問い合わせを閲覧；店舗/倉庫スタッフは`to_relation`で自拠点宛のみ閲覧。権限（`authority=guest`のゲストクエリ含む）、店舗、倉庫、ステータスでフィルター対応。**ゲスト問い合わせ**（`from_user=NULL`かつ`from_authority=NULL`）は`Inquiry.get_from_authority_display()`で「ゲスト」と表示。
- **問い合わせ送信** (`inquiry_create`, `InquiryCreateView`) — ログイン済みの非管理者ユーザー向け。`to_relation`フィールドはユーザーの店舗/倉庫に連携された関係のみ表示；`label_from_instance`で相手方名のみ表示（店舗スタッフは倉庫名、倉庫スタッフは店舗名）。`?relation=<id>`クエリパラメータ（連携倉庫一覧ページからなど）で`to_authority`と`to_relation`を事前入力。
- **ゲスト問い合わせ** (`inquiry_create_guest`, `InquiryGuestCreateView`) — 未認証ユーザー向け；常に管理者権限宛に送信。
- **問い合わせ詳細・ステータス更新** (`inquiry_detail/<pk>/`, `InquiryDetailView`) — 受信者はステータス更新可（未対応/対応中/対応済み）；送信者は閲覧のみ。
- **論理削除** (`inquiry_delete/<pk>/`, `InquiryDeleteView`) — 送信者または受信者が論理削除（`delete_flg=True`）可能。

## 問い合わせカテゴリ管理（管理者のみ）

- **InquiryCategoryモデル** — 問い合わせを分類。ソフトデリート対応のため`BaseModel`を継承。`condition=Q(delete_flg=False)`付きの`UniqueConstraint`とモデルレベルの`clean()`バリデーションでカテゴリ名のユニーク制約を適用（大文字小文字区別、未削除レコードのみ）。削除前に問い合わせとの紐づきを確認する`has_related_records()`メソッドを提供。
- **カテゴリ一覧** (`categories/`, `inquiry_category_list`, `InquiryCategoryListView`) — 管理者専用ビュー。有効な問い合わせカテゴリを名前順で一覧表示。
- **カテゴリ作成** (`categories/create/`, `inquiry_category_create`, `InquiryCategoryCreateView`) — 管理者が新カテゴリを作成。`next`パラメータによるインライン作成対応（GoodsCategoryと同パターン）。
- **カテゴリ編集** (`categories/<pk>/edit/`, `inquiry_category_edit`, `InquiryCategoryUpdateView`) — 管理者がカテゴリ名を更新。テンプレートに`can_delete`コンテキストフラグを表示。
- **カテゴリ削除** (`categories/<pk>/delete/`, `inquiry_category_delete`, `InquiryCategoryDeleteView`) — 管理者がカテゴリを論理削除。削除前に`has_related_records()`をチェック。
- **カテゴリ選択（問い合わせ作成時）** — `InquiryCreateView`と`InquiryGuestCreateView`はいずれも`inquiry_category`を必須フィールドとして含む。
- **カテゴリフィルター（問い合わせ一覧）** — `InquiryListView`は`?category=<id>`クエリパラメータで受信・送信両方の問い合わせをカテゴリフィルター対応。
