FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install --upgrade pip && \
    pip install --default-timeout=200 --no-cache-dir -r requirements.txt

EXPOSE 5000

CMD ["python", "app.py"]