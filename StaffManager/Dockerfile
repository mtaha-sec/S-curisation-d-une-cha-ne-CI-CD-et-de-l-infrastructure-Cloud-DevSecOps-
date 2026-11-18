FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && groupadd --system appgroup \
    && useradd --system --gid appgroup --home-dir /app appuser \
    && mkdir -p /data \
    && chown -R appuser:appgroup /app /data

COPY --chown=appuser:appgroup . .

USER appuser
EXPOSE 5000

CMD ["python", "app.py"]
