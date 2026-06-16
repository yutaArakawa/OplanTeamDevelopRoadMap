FROM python:3.12

WORKDIR /app

ENV TZ=Asia/Tokyo
ENV PYTHONPATH=/app
ENV DJANGO_SETTINGS_MODULE=config.settings
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    libffi-dev \
    libssl-dev \
    default-libmysqlclient-dev \
    build-essential \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    libfreetype6-dev \
    pkg-config \
    gcc \
    cron \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip setuptools wheel \ 
    && pip install --no-cache-dir -r requirements.txt

COPY . .

# crontab ファイルをコピーしてシステムレベルで登録
COPY batch/crontab /etc/cron.d/app-cron
RUN chmod 0644 /etc/cron.d/app-cron

# ログファイル用ディレクトリを作成
RUN touch /var/log/cron.log

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]