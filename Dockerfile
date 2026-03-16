FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY Backend ./Backend

ENV PYTHONUNBUFFERED=1

# Railway provides PORT at runtime; default to 8080 locally.
CMD ["sh", "-c", "gunicorn Backend.Lexical.main:app --bind 0.0.0.0:${PORT:-8080}"]
