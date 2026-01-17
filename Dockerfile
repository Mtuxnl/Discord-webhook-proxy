FROM python:3.9-alpine

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    find /usr/local -name '__pycache__' -type d -exec rm -rf {} +

COPY app.py .

EXPOSE 5001

CMD ["python", "app.py"]
