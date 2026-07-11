FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir \
    fastapi==0.115.0 \
    uvicorn==0.30.0 \
    python-multipart==0.0.9 \
    chromadb==1.5.9 \
    rank-bm25==0.2.2 \
    openai==1.82.0 \
    python-dotenv==1.0.1 \
    sentence-transformers==3.0.1 \
    cohere==5.15.0 \
    pymupdf==1.24.2 \
    nltk==3.8.1 \
    python-docx==1.1.2

RUN pip show nltk

RUN python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"

COPY src/ ./src/
COPY app/ ./app/
COPY data/raw/ ./data/raw/
COPY eval/ ./eval/

RUN python src/chunker.py && python src/embed.py

EXPOSE 7860

CMD ["python", "app/main.py"]