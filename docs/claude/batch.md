# バッチ処理・デプロイ

## 定期バッチ処理

**月次注文サマリー更新バッチ** (`update_monthly_order_summary` managementコマンド) — 店舗/商品ごとの日次注文データを`MonthlyOrderSummary`レコードに集計してレポートと分析に使用。

### Managementコマンド (`dashboard/management/commands/update_monthly_order_summary.py`)

- `order_filter_by_date_and_status()`で当日作成の注文をクエリ
- (店舗, 商品)ごとにグループ化して`OrderGoods.quantity`の合計を集計
- 再実行時の重複防止のため当日のレコードを削除（`MonthlyOrderSummary.objects.filter(count_date=today).delete()`）
- `atomic()`トランザクションで原子性を保証
- 1回のデータベース操作で`MonthlyOrderSummary`レコードをバルク作成

### Cronスケジューリング

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

### Bashスクリプト (`batch/run_monthly_order_summary.sh`)

- ファイル冒頭で環境変数をエクスポート（Unix標準）
- コマンド失敗時に即終了する`set -e`を使用
- JSTタイムゾーンでバッチ開始・終了時刻をログ出力

### Docker/Compose設定

- **Dockerfile**：
  - タイムスタンプ一貫性のため`ENV TZ=Asia/Tokyo`
  - `COPY batch/crontab /etc/cron.d/app-cron`でcrontabをイメージに組み込み
  - `RUN chmod 0644 /etc/cron.d/app-cron`でcronデーモンが読み取れるよう権限設定
- **docker-compose.yml**（cronサービス）：
  - コンテナ継続稼働に必要な`command: cron -f`でcronをフォアグラウンド実行
  - 冗長性のため環境変数に`TZ=Asia/Tokyo`
  - データベース準備完了を保証するため`db`サービスに依存

### テスト (`dashboard/tests.py::TestUpdateMonthlyOrderSummary`)

- `test_command_executes_successfully()` — コマンドがエラーなく実行されることを確認
- `test_creates_monthly_summary_records()` — `MonthlyOrderSummary`レコードが作成されることを確認
- `test_no_duplicate_records_on_multiple_executions()` — 削除ロジックで重複が防止されることを確認
- `test_summary_data_accuracy()` — 集計された`total_quantity`が正確なことを確認

---

## デプロイ注意事項

- **本番スケジュールの変更**：`batch/crontab` 6行目を`0 * * * *`（毎時）から`0 23 * * *`（23時日次）に変更
- **crontabの変更はリビルドが必要**：crontabはDockerfileに組み込まれているため、スケジュール変更には`docker-compose down && docker-compose up -d --build`が必要
- **ログの監視**：`docker-compose exec cron tail -f /var/log/cron.log`
- **手動テスト実行**：`docker-compose exec cron bash /app/batch/run_monthly_order_summary.sh`
