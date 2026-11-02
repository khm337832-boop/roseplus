FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DB_PATH=/app/data/roseplus.db

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /app/data
VOLUME ["/app/data"]

# PORT မပေးထားရင် 7860 (Hugging Face Spaces default) ကို သုံးမယ်
CMD ["sh", "-c", "PORT=${PORT:-7860} exec python bot.py"]
