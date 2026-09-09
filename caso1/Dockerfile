# Node 22 ejecuta los componentes JavaScript requeridos por yt-dlp para YouTube.
FROM node:22-bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-venv ffmpeg ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PATH="/opt/venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN python3 -m venv /opt/venv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py downloader.py ./
COPY templates/ templates/
COPY static/ static/

RUN useradd --create-home --uid 1001 appuser
USER appuser
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health', timeout=2)" || exit 1
CMD ["python", "app.py"]
