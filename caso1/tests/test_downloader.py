import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from downloader import DownloadError, download_video, run_command, validate_url


class DownloadTests(unittest.TestCase):
    def test_platforms_and_subdomains(self):
        for url, platform in (
            ("https://youtu.be/example", "YouTube"),
            ("https://www.instagram.com/reel/example/", "Instagram"),
            ("https://vm.tiktok.com/example/", "TikTok"),
            ("https://fb.watch/example/", "Facebook"),
            ("https://www.linkedin.com/posts/example", "LinkedIn"),
        ):
            self.assertEqual(validate_url(url)[1], platform)

    def test_rejects_arbitrary_urls_and_spoofed_domains(self):
        for url in ("", "file:///etc/passwd", "http://127.0.0.1/", "https://youtube.com.evil.test/x",
                    "https://youtube.com@evil.test/x", "https://youtube.com:999/x", "https://[broken",
                    "https://youtube.com/\nfoo"):
            with self.subTest(url=url), self.assertRaises(DownloadError):
                validate_url(url)

    def test_stream_file_exists_only_inside_context(self):
        def fake_download(command, timeout):
            self.assertEqual(command[-2:], ["--", "https://youtu.be/example"])
            self.assertIn("--no-playlist", command)
            output = command[command.index("--output") + 1]
            Path(output.replace("%(ext)s", "mp4")).write_bytes(b"test-video")
        with patch("downloader.run_command", side_effect=fake_download):
            with download_video("https://youtu.be/example") as path:
                self.assertEqual(path.read_bytes(), b"test-video")
                directory = path.parent
            self.assertFalse(directory.exists())

    def test_empty_success_is_not_a_video(self):
        with patch("downloader.run_command"), self.assertRaises(DownloadError):
            with download_video("https://youtu.be/example"):
                self.fail("No debe devolver una descarga inexistente")

    def test_failure_cleans_temporary_files(self):
        directories = []
        def fail(command, timeout):
            directory = Path(command[command.index("--output") + 1]).parent
            directories.append(directory)
            (directory / "video.mp4.part").write_bytes(b"partial")
            raise DownloadError("Error de plataforma")
        with patch("downloader.run_command", side_effect=fail), self.assertRaises(DownloadError):
            with download_video("https://youtu.be/example"):
                pass
        self.assertFalse(directories[0].exists())

    def test_timeout_kills_process_group(self):
        with patch("downloader.subprocess.Popen") as popen, patch("downloader.os.killpg") as kill:
            process = popen.return_value.__enter__.return_value
            process.pid = 4567
            process.communicate.side_effect = [subprocess.TimeoutExpired("yt-dlp", 180), (None, "")]
            with self.assertRaises(DownloadError):
                run_command(["yt-dlp"], 180)
            self.assertEqual(kill.call_args.args[0], 4567)


if __name__ == "__main__":
    unittest.main()
