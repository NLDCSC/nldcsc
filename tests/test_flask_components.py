from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from flask import Flask

from nldcsc.flask_managers.flask_app_manager import (
    FlaskAppManager,
    StandaloneApplication,
)
from nldcsc.flask_plugins.flask_eswrap import FlaskEsWrap
from nldcsc.flask_plugins.flask_kafka import FlaskKafka
from nldcsc.flask_plugins.flask_redis import FlaskRedis
from nldcsc.plugins.redis_client.wrapper import RedisWrapper


def test_standalone_application_loads_supported_configuration():
    app = Flask(__name__)
    server = StandaloneApplication(app, {"bind": "127.0.0.1:5000", "unknown": "ignored"})

    assert server.load() is app
    assert server.cfg.bind == ["127.0.0.1:5000"]


def test_flask_app_manager_reads_settings_and_runs_debug_server(monkeypatch):
    monkeypatch.setenv("DEBUG", "True")
    monkeypatch.setenv("DEBUG_WITH_SSL", "True")
    monkeypatch.setenv("BIND_HOST", "127.0.0.1")
    monkeypatch.setenv("BIND_PORT", "5010")
    app = Flask(__name__)
    app.run = Mock()

    manager = FlaskAppManager(version="1", app=app, workers=3)
    manager.run()

    assert manager.kwargs == {"workers": 3}
    app.run.assert_called_once_with(
        host="127.0.0.1", port=5010, ssl_context="adhoc"
    )


def test_flask_app_manager_uses_gunicorn_and_validates_workers(monkeypatch):
    monkeypatch.setenv("DEBUG", "False")
    app = Flask(__name__)
    server = Mock()
    standalone = Mock(return_value=server)
    monkeypatch.setattr(
        "nldcsc.flask_managers.flask_app_manager.StandaloneApplication",
        standalone,
    )
    manager = FlaskAppManager(version="1", app=app, bind="0.0.0.0:8000")
    manager._number_of_workers = Mock(return_value=2)
    manager.run()

    standalone.assert_called_once()
    options = standalone.call_args.args[1]
    assert options["bind"] == "0.0.0.0:8000"
    assert options["workers"] == 2
    server.run.assert_called_once_with()

    manager.worker_class = "unsupported"
    with pytest.raises(ValueError, match="Unsupported worker_class"):
        manager.run()


def test_flask_app_manager_runs_socketio_and_uses_configured_worker_count(monkeypatch):
    monkeypatch.setenv("DEBUG", "False")
    app = Flask(__name__)
    socketio = Mock()
    manager = FlaskAppManager(version="1", app=app, socketio=socketio, log_output=False)
    manager.max_workers = 4
    manager.run()

    socketio.run.assert_called_once()
    assert socketio.run.call_args.kwargs["app"] is app
    assert socketio.run.call_args.kwargs["log_output"] is False
    assert manager._number_of_workers() == 4


def test_flask_app_manager_rejects_non_flask_application():
    with pytest.raises(AttributeError, match="not of type 'Flask'"):
        FlaskAppManager(version="1", app=object())


def test_redis_wrapper_builds_client_from_url_and_environment(monkeypatch):
    client = Mock()
    redis_constructor = Mock(return_value=client)
    monkeypatch.setattr("nldcsc.plugins.redis_client.wrapper.redis.Redis", redis_constructor)
    monkeypatch.setenv("REDIS_CACHE_DB", "3")
    monkeypatch.setenv("REDIS_KWARGS", '{"decode_responses": true}')

    wrapper = RedisWrapper("redis://cache.test:6380/2", retry_on_timeout=True)

    redis_constructor.assert_called_once_with(
        host="cache.test",
        port=6380,
        db=3,
        retry_on_timeout=True,
        decode_responses=True,
    )
    assert wrapper.redis_client is client
    assert wrapper.get is client.get
    assert repr(wrapper) == "<< RedisWrapper >>"


def test_flask_redis_registers_wrapper_without_connecting(monkeypatch):
    connect = Mock()
    monkeypatch.setattr(RedisWrapper, "connect", connect)
    app = Flask(__name__)

    wrapper = FlaskRedis(app, redis_url="redis://cache.test:6379/0")

    connect.assert_called_once()
    assert app.redis_client is wrapper
    assert repr(wrapper) == "<< FlaskRedis >>"
    with pytest.raises(Exception, match="App must be None"):
        FlaskRedis(app, init_standalone=True)


def test_flask_kafka_builds_producer_and_consumer(monkeypatch):
    producer = Mock()
    consumer = Mock()
    producer.bootstrap_connected.return_value = True
    consumer.bootstrap_connected.return_value = True
    monkeypatch.setattr(
        "nldcsc.flask_plugins.flask_kafka.KafkaProducer",
        Mock(return_value=producer),
    )
    monkeypatch.setattr(
        "nldcsc.flask_plugins.flask_kafka.KafkaConsumer",
        Mock(return_value=consumer),
    )
    app = Flask(__name__)
    wrapper = FlaskKafka(app, client_id="test")

    assert app.producer is producer
    assert app.consumer is consumer
    assert wrapper.producer is producer
    assert wrapper.consumer is consumer
    assert repr(wrapper) == "<< FlaskKafka >>"


def test_flask_eswrap_initializes_and_wraps_compatibility_headers(monkeypatch):
    client = Mock()

    class Transport:
        def perform_request(self, *args, **kwargs):
            return kwargs

    transport = Transport()
    client.es_client = SimpleNamespace(transport=transport)

    eswrap = Mock(return_value=client)
    monkeypatch.setattr("nldcsc.flask_plugins.flask_eswrap.EsWrap", eswrap)
    monkeypatch.setattr(
        "nldcsc.flask_plugins.flask_eswrap.getenv_list", Mock(return_value=[])
    )
    monkeypatch.setattr(
        "nldcsc.flask_plugins.flask_eswrap.getenv_dict", Mock(return_value=None)
    )
    monkeypatch.setenv("ELASTIC_COMPAT_VERSION", "8")
    monkeypatch.setenv("ELASTIC_USER", "user")
    monkeypatch.setenv("ELASTIC_PASSWORD", "password")
    app = Flask(__name__)

    wrapper = FlaskEsWrap(app, request_timeout=5)

    assert app.flask_eswrap is wrapper
    eswrap.assert_called_once_with(
        host="localhost",
        port=9200,
        scheme="http",
        http_auth=("user", "password"),
        request_timeout=5,
    )
    result = transport.perform_request(
        "GET",
        "/",
        headers={
            "accept": "application/json",
            "Content-Type": "application/vnd.elasticsearch+json",
            "Other": "application/json",
        },
    )
    assert result["headers"] == {
        "accept": "application/vnd.elasticsearch+json; compatible-with=8",
        "Content-Type": "application/vnd.elasticsearch+json; compatible-with=8",
        "Other": "application/json",
    }


def test_flask_eswrap_rejects_conflicting_standalone_app(monkeypatch):
    monkeypatch.setattr(
        "nldcsc.flask_plugins.flask_eswrap.getenv_list", Mock(return_value=[])
    )
    monkeypatch.setattr(
        "nldcsc.flask_plugins.flask_eswrap.getenv_dict", Mock(return_value=None)
    )
    monkeypatch.setattr(FlaskEsWrap, "__del__", lambda self: None)
    with pytest.raises(Exception, match="App must be None"):
        FlaskEsWrap(Flask(__name__), init_standalone=True)
