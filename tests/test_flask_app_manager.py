import threading

import pytest
import requests
from flask import Flask

from nldcsc.flask_managers.flask_app_manager import FlaskAppManager


class StoppableThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        """constructor, setting initial variables"""
        self._stopevent = threading.Event()
        self._sleepperiod = 1.0
        threading.Thread.__init__(self, *args, **kwargs)

    def run(self):
        """main control loop"""
        count = 0
        while not self._stopevent.is_set():
            count += 1
            self._stopevent.wait(self._sleepperiod)

    def join(self, timeout=None):
        """Stop the thread and wait for it to end."""
        self._stopevent.set()
        threading.Thread.join(self, timeout)


app = Flask(__name__)


@app.route("/")
def index():
    return "SUCCESS"


@pytest.fixture(scope="session")
def runner():
    fam = FlaskAppManager(version="TEST_VERSION", app=app)

    t = StoppableThread(target=fam.run)
    yield t.start()

    t.join()


class TestFlaskAppManager:
    def test_init(self):
        fam = FlaskAppManager(version="TEST_VERSION", app=app)

        assert isinstance(fam, FlaskAppManager)

    def test_web(self, runner):

        with requests.Session() as session:
            r = session.get("http://localhost:5050")

        assert r.status_code == 200
        assert r.content == b"SUCCESS"
