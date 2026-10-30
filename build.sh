#!/usr/bin/env bash
# Render 部署時自動執行：安裝套件 → 收集靜態檔 → 建立資料表 → 匯入示範資料與帳號
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py seed_data
