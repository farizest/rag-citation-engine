# ── base image ────────────────────────────────────────────────
FROM python:3.10-slim

# ── set working directory ─────────────────────────────────────
WORKDIR /app

# ── install system dependencies ───────────────────────────────
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# ── copy and install python dependencies ──────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── download NLTK data ────────────────────────────────────────
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"

# ── copy project files ────────────────────────────────────────
COPY src/ ./src/
COPY app/ ./app/
COPY data/raw/ ./data/raw/
COPY eval/ ./eval/

# ── pre-build the pipeline ────────────────────────────────────
RUN python src/chunker.py && python src/embed.py

# ── expose port ───────────────────────────────────────────────
EXPOSE 7860

# ── start the app ─────────────────────────────────────────────
CMD ["python", "app/main.py"]