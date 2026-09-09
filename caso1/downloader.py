"""Descarga de un video por solicitud; archivos temporales aislados."""

from contextlib import contextmanager
from pathlib import Path
import os
import signal
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit


PLATFORMS = {
    "YouTube": ("youtube.com", "youtu.be"),
    "Instagram": ("instagram.com",),
    "TikTok": ("tiktok.com",),
    "Facebook": ("facebook.com", "fb.watch"),
    "LinkedIn": ("linkedin.com",),
}
MAX_BYTES = 200 * 1024 * 1024
TIMEOUT_SECONDS = 180


class DownloadError(Exception):
    """Error que puede mostrarse al usuario."""


def validate_url(value):
    url = value.strip()
    if not url or len(url) > 4096 or any(ord(c) < 32 for c in url):
        raise DownloadError("Introduce un enlace de video válido.")
    try:
        parsed = urlsplit(url)
        host = (parsed.hostname or "").lower()
        if (parsed.scheme not in ("http", "https") or parsed.username
                or parsed.password or parsed.port not in (None, 80, 443)):
            raise ValueError
    except ValueError:
        raise DownloadError("Usa una URL http o https sin credenciales ni puertos especiales.") from None
    for platform, domains in PLATFORMS.items():
        if any(host == domain or host.endswith("." + domain) for domain in domains):
            return url, platform
    raise DownloadError("El enlace debe pertenecer a YouTube, Instagram, TikTok, Facebook o LinkedIn.")


def run_command(command, timeout):
    """Al expirar, finaliza también FFmpeg y los demás procesos hijos en Linux."""
    with subprocess.Popen(
        command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace", start_new_session=True,
    ) as process:
        try:
            _, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.communicate()
            raise DownloadError("La descarga superó los 3 minutos. Prueba con un video más corto.") from None
        if process.returncode != 0:
            detail = "\n".join(stderr.strip().splitlines()[-4:])[-1500:]
            raise DownloadError("La plataforma no permitió completar la descarga. " + detail)


@contextmanager
def download_video(url):
    url, _ = validate_url(url)
    with tempfile.TemporaryDirectory(prefix="caso1-") as directory:
        command = [
            sys.executable, "-m", "yt_dlp", "--ignore-config", "--no-plugin-dirs",
            "--no-playlist", "--playlist-items", "1", "--no-progress", "--no-warnings",
            "--no-colors", "--socket-timeout", "20", "--retries", "2",
            "--fragment-retries", "2", "--js-runtimes", "node",
            "--max-filesize", str(MAX_BYTES), "--no-cache-dir",
            "--format", "bv*+ba/b", "--format-sort", "res:720",
            "--merge-output-format", "mp4", "--output", str(Path(directory) / "video.%(ext)s"),
            "--", url,
        ]
        run_command(command, TIMEOUT_SECONDS)
        files = [p for p in Path(directory).iterdir()
                 if p.is_file() and not p.is_symlink()
                 and p.suffix.lower() in (".mp4", ".webm", ".mkv", ".mov", ".flv", ".avi", ".3gp")]
        if len(files) != 1:
            raise DownloadError("No se obtuvo un único video completo. Puede ser un enlace no compatible o un archivo demasiado grande.")
        video = files[0]
        if not 0 < video.stat().st_size <= MAX_BYTES:
            raise DownloadError("El video está vacío o supera el límite de 200 MiB.")
        yield video
