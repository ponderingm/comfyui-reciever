FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY drive_fetcher.py /app/drive_fetcher.py
# /creds と /downloads をボリュームとして使う想定
ENV GOOGLE_APPLICATION_CREDENTIALS=/creds/service_account.json
ENV DOWNLOAD_DIR=/downloads
CMD ["python", "/app/drive_fetcher.py"]
