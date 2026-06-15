# Python Stock App - 小売在庫管理システム

複数の店舗と倉庫を管理する小売企業向けの Django ベース在庫管理・注文システム。複数拠点の在庫状況をリアルタイムに把握し、店舗から倉庫への発注業務を効率化します。

## システム概要

### 主な機能

- **店舗在庫管理** — 各店舗の商品在庫を一元管理
- **倉庫管理** — 複数倉庫の在庫追跡
- **発注フロー** — 店舗スタッフから倉庫への注文・受注管理
- **月次集計** — 注文データの日次集計（毎日 23:00）
- **問い合わせシステム** — 店舗と倉庫間の連携
- **ロールベース権限** — 管理者/店舗スタッフ/倉庫スタッフの 3 役割

### 技術スタック

- **Backend**: Django 6.0.5
- **Database**: MySQL 8.0（本番）/ SQLite（テスト）
- **Container**: Docker & Docker Compose
- **Batch Jobs**: Linux cron（Docker コンテナ内）
- **Testing**: pytest + pytest-django

---

## セットアップ

### 前提条件

- Docker & Docker Compose
- Python 3.12（ローカル開発時）

### インストール

```bash
# リポジトリをクローン
git clone <repository-url>
cd python_stock_app

# .env ファイルを作成（値はチームメンバーから入手）
cp .env.example .env

# Docker コンテナを起動（開発環境）
docker compose -f docker-compose.dev.yml up -d
```

**アクセス:**
- Web アプリ: http://localhost（ポート80）
- MySQL: localhost:3307

---

## 開発環境

### コンテナの起動・停止

docker composeコマンドには必ず `-f docker-compose.dev.yml`（開発）または `-f docker-compose.prod.yml`（本番）を指定してください。

```bash
# 起動（開発環境）
docker compose -f docker-compose.dev.yml up -d

# 停止（開発環境）
docker compose -f docker-compose.dev.yml down

# ログ確認
docker compose -f docker-compose.dev.yml logs -f web     # Webアプリケーション
docker compose -f docker-compose.dev.yml logs -f cron    # 定時バッチ
docker compose -f docker-compose.dev.yml logs -f db      # データベース
```

### ローカル開発（Docker 不使用）

```bash
# 依存関係をインストール
pip install -r requirements.txt

# マイグレーション実行（SQLite 使用）
CI=true python manage.py migrate

# 開発サーバー起動
CI=true python manage.py runserver
```

### スーパーユーザー作成

```bash
# Docker コンテナ内の場合
docker compose exec web python manage.py createsuperuser

# ローカル開発の場合
CI=true python manage.py createsuperuser
```

**注意**: スーパーユーザー作成には `Authority` テーブルに `id=1` が存在する必要があります（初期化済み）。

---

## テスト実行

### 全テスト実行

```bash
# Docker コンテナ内（推奨）
docker compose exec -e CI=true web pytest

# ローカル環境
CI=true pytest
```

### 特定アプリのテストのみ実行

```bash
# 例: accounts アプリのテスト
docker compose exec -e CI=true web pytest accounts/

# 例: ダッシュボードのテスト
docker compose exec -e CI=true web pytest dashboard/tests.py
```

### 特定のテストクラス・メソッドを実行

```bash
# テストクラス実行
docker compose exec -e CI=true web pytest dashboard/tests.py::TestDashboard -v

# テストメソッド実行
docker compose exec -e CI=true web pytest dashboard/tests.py::TestDashboard::test_admin_get_200 -v
```

---

## 定時バッチジョブ

### 月次注文サマリー集計バッチ

毎日 **23:00** に自動実行され、その日の注文データを商品ごとに集計して `MonthlyOrderSummary` テーブルに保存します。

**実行内容:**
- 当日の全注文を店舗・商品単位で集計
- 注文数の合計を計算し、月次サマリーレコードを作成
- 重複防止のため既存レコード削除後に再作成

**実装ファイル:**
- `dashboard/management/commands/update_monthly_order_summary.py` — バッチコマンド
- `batch/run_monthly_order_summary.sh` — 実行スクリプト（ログ記録付き）
- `batch/crontab` — cron スケジュール設定

### ログ確認

バッチ実行ログはコンテナ内の `/var/log/cron.log` に出力されます。

```bash
# リアルタイムログ確認
docker compose exec cron tail -f /var/log/cron.log

# ログ全体表示
docker compose exec cron cat /var/log/cron.log
```

**ログ出力例:**
```
バッチ開始: 月次注文サマリーの更新 Wed Jun  3 23:00:01 JST 2026
月次の注文数集計が更新されました。
バッチ終了: 月次注文サマリーの更新 Wed Jun  3 23:00:02 JST 2026
```

---

## 開発時：バッチ実行時間の変更

開発/テスト時にバッチの実行時間を変更して動作確認できます。

### 方法 1：コンテナ内で直接編集（推奨・即座に反映）

テスト時間を指定したい場合（例：14:30 に実行させる）：

```bash
docker compose exec cron bash -c 'cat > /etc/cron.d/app-cron << EOF
# スケジュールバッチジョブ用システムcrontab
# cron実行環境の環境変数
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
TZ=Asia/Tokyo
PYTHONPATH=/app
DJANGO_SETTINGS_MODULE=config.settings

# 月次注文サマリー集計バッチ
30 14 * * * root bash /app/batch/run_monthly_order_summary.sh >> /var/log/cron.log 2>&1
EOF'
```

**実行時刻の指定形式:**
```
分 時 日 月 曜日 ユーザー コマンド

0 14 * * * — 毎日 14:00 に実行
30 14 * * * — 毎日 14:30 に実行
*/5 * * * * — 5 分ごとに実行（テスト用）
```

### 動作確認

1. **ログをクリア:**
   ```bash
   docker compose exec cron bash -c 'echo "" > /var/log/cron.log'
   ```

2. **ログを監視:**
   ```bash
   docker compose exec cron tail -f /var/log/cron.log
   ```

3. **指定時間を待機** — 次の実行時刻にバッチが自動実行されます

4. **手動実行で確認（時間を待たずにテスト）:**
   ```bash
   docker compose exec cron bash /app/batch/run_monthly_order_summary.sh
   ```

### 本番設定（23:00）に戻す

テスト終了後は本番設定に戻してください：

```bash
docker compose exec cron bash -c 'cat > /etc/cron.d/app-cron << EOF
# スケジュールバッチジョブ用システムcrontab
# cron実行環境の環境変数
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
TZ=Asia/Tokyo
PYTHONPATH=/app
DJANGO_SETTINGS_MODULE=config.settings

# 月次注文サマリー集計バッチ
0 23 * * * root bash /app/batch/run_monthly_order_summary.sh >> /var/log/cron.log 2>&1
EOF'
```

### 方法 2：ホスト側ファイル修正 → rebuild（永続的な変更用）

本番環境に反映する場合は以下の手順を使用します：

```bash
# 1. ホスト側のファイル編集
#    batch/crontab 行 9 を編集（例: 0 23 * * * → 0 14 * * *）

# 2. コンテナを再ビルド・起動
docker compose -f docker-compose.dev.yml down
docker compose -f docker-compose.dev.yml up -d --build

# 3. 修正確認
docker compose exec cron cat /etc/cron.d/app-cron
```

---

## マイグレーション

### マイグレーションの作成・実行

```bash
# 新しいマイグレーション作成
docker compose exec web python manage.py makemigrations

# マイグレーション実行
docker compose exec web python manage.py migrate

# マイグレーション状態確認
docker compose exec web python manage.py showmigrations
```

### ローカル環境

```bash
CI=true python manage.py makemigrations
CI=true python manage.py migrate
```

---

## データベース管理

### MySQL コンテナにアクセス

```bash
# MySQL コマンドラインでアクセス
docker compose exec db mysql -u stockuser -ppassword stockdb

# SQL クエリ実行例
docker compose exec db mysql -u stockuser -ppassword stockdb -e "SELECT * FROM inventory_goods LIMIT 5;"
```

### データベースリセット

```bash
# すべてのコンテナを停止・削除
docker compose -f docker-compose.dev.yml down -v

# コンテナを再起動（フレッシュデータベースで開始）
docker compose -f docker-compose.dev.yml up -d
```

**注意:** `-v` フラグはボリューム（MySQL データ）を削除します。本番環境では実行しないでください。

---

## トラブルシューティング

### Port Already in Use エラー

```bash
# ポート確認・終了
lsof -i :80        # ポート 80 のプロセス確認
kill -9 <PID>      # プロセス終了

# または Docker を再起動
docker compose -f docker-compose.dev.yml down
docker compose -f docker-compose.dev.yml up -d
```

### データベース接続エラー

```bash
# データベースがヘルシーか確認
docker compose -f docker-compose.dev.yml ps    # "healthy" ステータスを確認

# コンテナのログ確認
docker compose -f docker-compose.dev.yml logs db

# 起動まで待機
docker compose -f docker-compose.dev.yml up -d
sleep 10
docker compose exec web python manage.py migrate
```

### バッチログが出力されない

```bash
# cron daemon が実行中か確認
docker compose exec cron ps aux | grep cron

# crontab が正しく設定されているか確認
docker compose exec cron cat /etc/cron.d/app-cron

# cron ログを確認
docker compose exec cron cat /var/log/cron.log
```

---

## アーキテクチャ詳細

詳細なアーキテクチャ・設計情報は **[CLAUDE.md](./CLAUDE.md)** を参照してください：

- 各アプリケーションの責務
- データモデル・ER図
- API エンドポイント構成
- 注文フロー（店舗 → 倉庫）
- 問い合わせシステム
- ロールベース権限設計
- テスト構成

---

## 本番環境へのデプロイ

### 環境変数設定

以下の環境変数を本番環境に設定してください：

```bash
DEBUG=False
ALLOWED_HOSTS=<本番ドメイン>
SECRET_KEY=<セキュアなシークレットキー>
DATABASE_URL=mysql://<ユーザー>:<パスワード>@<ホスト>:3306/<DB名>
```

### Docker イメージビルド・デプロイ

```bash
# イメージビルド
docker build -t python_stock_app:latest .

# レジストリへプッシュ
docker tag python_stock_app:latest <レジストリ>/python_stock_app:latest
docker push <レジストリ>/python_stock_app:latest

# 本番サーバーでデプロイ
docker pull <レジストリ>/python_stock_app:latest
docker compose -f docker-compose.prod.yml up -d
```

### crontab スケジュール確認

本番環境でバッチが 23:00 に実行されるか確認：

```bash
docker compose exec cron cat /etc/cron.d/app-cron
# 出力に "0 23 * * *" が含まれることを確認
```

---

## ライセンス

プロプライエタリ - 内部利用のみ

---

## サポート

問題が発生した場合は、以下を確認してください：

1. **ログの確認** — `docker compose -f docker-compose.dev.yml logs -f`
2. **コンテナの状態** — `docker compose -f docker-compose.dev.yml ps`
3. **アーキテクチャドキュメント** — `CLAUDE.md`
4. **テストの実行** — `docker compose exec -e CI=true web pytest -v`

詳細はプロジェクト内の `CLAUDE.md` を参照してください。
