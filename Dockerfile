FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"

COPY src/ ./src/
COPY app/ ./app/
COPY data/raw/ ./data/raw/
COPY eval/ ./eval/

RUN python src/chunker.py && python src/embed.py

EXPOSE 7860

CMD ["python", "app/main.py"]