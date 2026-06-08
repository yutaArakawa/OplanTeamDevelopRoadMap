#!/bin/bash
set -e

echo "=== マイグレーション実行 ==="
python manage.py migrate

echo "=== マスタデータ投入 & スーパーユーザー作成 ==="
python manage.py seed_master

echo "=== 開発サーバー起動 ==="
exec python manage.py runserver 0.0.0.0:8000
