# Dockerfile
FROM python:3.10-slim as builder

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && apt-get install -y libsnappy-dev
RUN pip install --no-cache-dir -r requirements.txt python-snappy

FROM python:3.10-slim

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages

COPY . .

CMD ["python", "main.py"]
