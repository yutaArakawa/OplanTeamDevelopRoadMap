#!/bin/bash

# エラーハンドリング
set -e

# ログ出力
echo "バッチ開始: MySQLバックアップ $(date)"

# バックアップ先ディレクトリ作成
BACKUP_DIR=/app/backup
mkdir -p $BACKUP_DIR

# バックアップ実行
FILE="${BACKUP_DIR}/backup_$(TZ=Asia/Tokyo date +%Y%m%d_%H%M%S).sql.gz"
mysqldump -h db -u ${DATABASES_USER} -p${DATABASES_PASSWORD} ${DATABASES_NAME} | gzip > $FILE

echo "バックアップ完了: $FILE"

# 30日以上古いファイルを削除
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "バッチ終了: MySQLバックアップ $(date)"
