FROM python:3.11-slim

WORKDIR /app

# System dependencies for psycopg2/pg_config if needed (using binary though)
RUN apt-get update && apt-get install -y libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source and seeds
COPY . .

# Run gunicorn for production
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8081", "app:app"]
