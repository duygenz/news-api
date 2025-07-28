FROM python:3.9-slim-buster

# Cài đặt các thư viện hệ thống cần thiết cho lxml
RUN apt-get update && \
    apt-get install -y \
    libxml2-dev \
    libxslt-dev \
    python3-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]
