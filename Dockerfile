FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ephemeris_data/ ./ephemeris_data/
COPY astro_engine/ ./astro_engine/
COPY compute_chart.py .

ENV PYTHONUNBUFFERED=1
ENV EPHEMERIS_PATH=/app/ephemeris_data

EXPOSE 8000

CMD ["uvicorn", "astro_engine.api:app", "--host", "0.0.0.0", "--port", "8000"]
