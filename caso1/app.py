"""Caso 1: formulario web para descargar videos de las cinco plataformas."""

import mimetypes
import shutil
from threading import BoundedSemaphore

from flask import Flask, Response, jsonify, render_template, request

from downloader import DownloadError, PLATFORMS, download_video, validate_url

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 8192
download_slots = BoundedSemaphore(2)


@app.get("/")
def index():
    return render_template("index.html", platforms=PLATFORMS)


@app.get("/health")
def health():
    missing = [name for name in ("ffmpeg", "ffprobe", "node") if not shutil.which(name)]
    return jsonify(status="error" if missing else "ok", missing=missing), 503 if missing else 200


@app.post("/download")
def download():
    try:
        url, platform = validate_url(request.form.get("url", ""))
    except DownloadError as error:
        return jsonify(error=str(error)), 400
    if not download_slots.acquire(blocking=False):
        return jsonify(error="Hay dos descargas en curso. Intenta nuevamente en unos minutos."), 429

    context = download_video(url)
    try:
        video = context.__enter__()
    except DownloadError as error:
        download_slots.release()
        return jsonify(error=str(error)), 422
    except Exception:
        download_slots.release()
        app.logger.exception("Error al preparar la descarga")
        return jsonify(error="No se pudo preparar la descarga. Revisa los logs del contenedor."), 500

    closed = False

    def cleanup():
        nonlocal closed
        if not closed:
            closed = True
            context.__exit__(None, None, None)
            download_slots.release()

    def stream():
        try:
            with video.open("rb") as source:
                while chunk := source.read(65536):
                    yield chunk
        finally:
            cleanup()

    response = Response(stream(), mimetype=mimetypes.guess_type(video.name)[0] or "application/octet-stream")
    response.headers["Content-Disposition"] = f'attachment; filename="{platform.lower()}-video{video.suffix}"'
    response.headers["Content-Length"] = str(video.stat().st_size)
    response.headers["Cache-Control"] = "no-store"
    response.call_on_close(cleanup)
    return response


@app.errorhandler(413)
def too_large(_error):
    return jsonify(error="La solicitud es demasiado grande. Introduce únicamente la URL del video."), 413


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
