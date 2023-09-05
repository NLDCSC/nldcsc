from flask import Flask

from nldcsc.flask_managers.flask_app_manager import FlaskAppManager

app = Flask(__name__)


@app.route("/")
def index():
    return "SUCCESS"


class TestFlaskAppManager:
    def test_init(self):
        fam = FlaskAppManager(version="TEST_VERSION", app=app)

        assert isinstance(fam, FlaskAppManager)
