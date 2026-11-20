"""Browser test (Playwright): the Failed tab's Export list button downloads the failed list.

Needs the Playwright Python package and a Chromium it can drive. Point YTDL_CHROME at a
Chrome/Chromium binary if Playwright's own browser isn't installed. Skips itself otherwise.
"""
import os
import socket
import tempfile
import threading
import unittest
from pathlib import Path

from tests import helpers  # noqa: F401
import web_server

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover - depends on the machine
    sync_playwright = None

FAILED = (
    "2026-11-19 09:00\tMusic\thttps://youtu.be/AAA\n"
    "2026-11-19 09:05\tPodcasts\thttps://youtu.be/BBB\n"
)


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class FakeRunner:
    """Just enough of the tray app's runner for the status endpoint."""
    status = "Idle"
    icon_state = "idle"
    cookie_problem = False
    next_run = None
    next_count = None
    last_flexget = None
    sched = None
    interval_minutes = 120

    def __init__(self):
        self.paused = threading.Event()

    def api_run_now(self):
        pass

    def api_pause(self):
        self.paused.set()

    def api_resume(self):
        self.paused.clear()


@unittest.skipIf(sync_playwright is None, "Playwright is not installed")
class ExportFailedListUiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.lists = self.tmp / "lists"; self.lists.mkdir()
        self.state = self.tmp / "state"; self.state.mkdir()
        (self.state / "failed.txt").write_text(FAILED, encoding="utf-8")
        self.port = free_port()
        self.srv, _ = web_server.start(FakeRunner(), {"host": "127.0.0.1", "port": self.port},
                                       self.state, self.lists, self.tmp / "tray.log",
                                       log=lambda *a: None)
        self.base = f"http://127.0.0.1:{self.port}"

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()

    def launch(self, p):
        opts = {"headless": True}
        if os.environ.get("YTDL_CHROME"):
            opts["executable_path"] = os.environ["YTDL_CHROME"]
        try:
            return p.chromium.launch(**opts)
        except Exception as e:  # browser not installed on this machine
            self.skipTest(f"No browser available for Playwright: {e}")

    def test_export_downloads_the_whole_failed_list(self):
        with sync_playwright() as p:
            browser = self.launch(p)
            try:
                page = browser.new_page(accept_downloads=True)
                page.goto(self.base)
                page.click('button.nav-btn[data-view="failed"]')
                page.wait_for_selector("#fa-list .item.failed")
                self.assertEqual(page.locator("#fa-list .item.failed").count(), 2)
                self.assertTrue(page.is_enabled("#fa-export"))
                with page.expect_download() as info:
                    page.click("#fa-export")
                download = info.value
                self.assertTrue(download.suggested_filename.startswith("failed-"))
                self.assertTrue(download.suggested_filename.endswith(".txt"))
                saved = self.tmp / "exported.txt"
                download.save_as(saved)
                self.assertEqual(saved.read_text(encoding="utf-8"), FAILED)
            finally:
                browser.close()

    def test_export_is_disabled_when_nothing_failed(self):
        (self.state / "failed.txt").write_text("", encoding="utf-8")
        with sync_playwright() as p:
            browser = self.launch(p)
            try:
                page = browser.new_page()
                page.goto(self.base)
                page.click('button.nav-btn[data-view="failed"]')
                page.wait_for_selector("#fa-list .card.empty")
                self.assertFalse(page.is_enabled("#fa-export"))
            finally:
                browser.close()


if __name__ == "__main__":
    unittest.main()
