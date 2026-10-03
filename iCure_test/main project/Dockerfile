FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# build tools needed to compile some Python packages (e.g. FAISS)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# install dependencies first so this layer is cached between builds
COPY requirements.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# apply database migrations, then start the production server
CMD ["sh", "-c", "alembic upgrade head && gunicorn --workers 1 --threads 4 --timeout 120 --bind 0.0.0.0:5000 app:app"]
