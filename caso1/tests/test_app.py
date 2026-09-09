from contextlib import contextmanager
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app import app
from downloader import DownloadError


class AppTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_home_and_invalid_link(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.post("/download", data={"url": "http://localhost/"}).status_code, 400)

    def test_download_stream_and_cleanup(self):
        directories = []
        @contextmanager
        def fake_download(_url):
            with tempfile.TemporaryDirectory() as directory:
                directories.append(Path(directory))
                video = Path(directory) / "video.mp4"
                video.write_bytes(b"simulated-video-for-test")
                yield video
        with patch("app.download_video", fake_download):
            response = self.client.post("/download", data={"url": "https://youtu.be/example"})
            self.assertEqual(response.status_code, 200)
            self.assertIn('youtube-video.mp4', response.headers["Content-Disposition"])
            self.assertEqual(response.data, b"simulated-video-for-test")
            response.close()
        self.assertFalse(directories[0].exists())

    def test_platform_error_is_visible(self):
        @contextmanager
        def failed_download(_url):
            raise DownloadError("Video no disponible")
            yield
        with patch("app.download_video", failed_download):
            response = self.client.post("/download", data={"url": "https://youtu.be/example"})
            self.assertEqual(response.status_code, 422)
            self.assertEqual(response.json["error"], "Video no disponible")


if __name__ == "__main__":
    unittest.main()
