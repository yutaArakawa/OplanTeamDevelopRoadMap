#!/bin/bash

# 環境変数を一番上に配置（推奨）
export PYTHONPATH=/app
export DJANGO_SETTINGS_MODULE=config.settings

# エラーハンドリング
set -e

# ログ出力
echo "バッチ開始: 月次注文サマリーの更新 $(date)"

# メイン処理
cd /app
python3 manage.py update_monthly_order_summary

echo "バッチ終了: 月次注文サマリーの更新 $(date)"
