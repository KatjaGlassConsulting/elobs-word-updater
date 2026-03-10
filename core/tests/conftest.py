from __future__ import annotations
import threading
import time
import pytest
import uvicorn
from tests.dummy_api.app import app as dummy_app

DUMMY_API_HOST = "127.0.0.1"
DUMMY_API_PORT = 18765
DUMMY_API_BASE = f"http://{DUMMY_API_HOST}:{DUMMY_API_PORT}"
DUMMY_API_URL = f"{DUMMY_API_BASE}/api"


class _ServerThread(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.server = uvicorn.Server(
            uvicorn.Config(dummy_app, host=DUMMY_API_HOST, port=DUMMY_API_PORT, log_level="error")
        )

    def run(self):
        self.server.run()

    def stop(self):
        self.server.should_exit = True


_server_thread: _ServerThread | None = None


@pytest.fixture(scope="session", autouse=True)
def dummy_api_server():
    global _server_thread
    _server_thread = _ServerThread()
    _server_thread.start()
    # Wait for server to be ready
    import httpx
    for _ in range(20):
        try:
            httpx.get(f"{DUMMY_API_URL}/studies", timeout=1)
            break
        except Exception:
            time.sleep(0.2)
    yield DUMMY_API_URL
    _server_thread.stop()


@pytest.fixture
def dummy_api_url(dummy_api_server):
    return dummy_api_server
