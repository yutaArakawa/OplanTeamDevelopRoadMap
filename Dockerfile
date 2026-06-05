FROM python:3.12

WORKDIR /app

ENV TZ=Asia/Tokyo
ENV PYTHONPATH=/app
ENV DJANGO_SETTINGS_MODULE=config.settings

RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    pkg-config \
    gcc \
    cron

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# crontab ファイルをコピーしてシステムレベルで登録
COPY batch/crontab /etc/cron.d/app-cron
RUN chmod 0644 /etc/cron.d/app-cron

# ログファイル用ディレクトリを作成
RUN touch /var/log/cron.log

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]