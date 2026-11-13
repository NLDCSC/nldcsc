import uuid as uuid_module

import pytest
from flask import Flask, Response
from sqlalchemy import String

from nldcsc.custom_types.sqlalchemy.annotations import str_64, uuid_pk
from nldcsc.custom_types.sqlalchemy.custom_types import char_UUID
from nldcsc.custom_types.sqlalchemy.model_base import ModelBase
from nldcsc.flask_midddleware.base import BaseHTTPMiddleware
from nldcsc.flask_midddleware.debug_logging import DebugLoggingMiddleware
from nldcsc.flask_midddleware.middleware_manager import MiddlewareManager


def test_uuid_type_converts_to_and_from_database_values():
    column_type = char_UUID()
    value = uuid_module.UUID("12345678-1234-5678-1234-567812345678")

    assert column_type.process_bind_param(value, None) == value.hex
    assert (
        column_type.process_bind_param("12345678-1234-5678-1234-567812345678", None)
        == value.hex
    )
    assert column_type.process_bind_param(None, None) is None
    assert column_type.process_result_value(value.hex, None) == str(value)
    assert column_type.process_result_value(None, None) is None


def test_model_base_maps_common_annotations():
    type_map = ModelBase.registry.type_annotation_map

    assert isinstance(type_map[str_64], String)
    assert type_map[str_64].length == 64
    assert type_map[uuid_pk] is char_UUID


class RecordingMiddleware(BaseHTTPMiddleware):
    def _before_request(self):
        self.app.config["before_called"] = True

    def _after_request(self, response: Response) -> Response:
        response.headers["X-Middleware"] = "active"
        return response


def test_middleware_hooks_and_manager_initialize_in_rank_order():
    app = Flask(__name__)
    manager = MiddlewareManager()
    manager.add_middleware(RecordingMiddleware, rank=10, app=app)
    manager.add_middleware(RecordingMiddleware, rank=1, app=app)

    assert [rank for rank, _ in manager.middleware_stack] == [10, 1]
    manager.init_app(app)
    app.add_url_rule("/", view_func=lambda: "ok")

    response = app.test_client().get("/")
    assert app.config["before_called"] is True
    assert response.headers["X-Middleware"] == "active"
    assert app.middleware_manager is manager
    assert repr(manager) == "<< MiddlewareManager >>"


def test_manager_rejects_classes_outside_middleware_hierarchy():
    manager = MiddlewareManager()

    with pytest.raises(Exception, match="not inherited"):
        manager.add_middleware(object, rank=1)


def test_debug_logging_middleware_logs_request_metadata():
    app = Flask(__name__)
    middleware = DebugLoggingMiddleware(app)
    records = []
    middleware.logger.info = records.append
    app.add_url_rule("/", view_func=lambda: "ok")

    response = app.test_client().get(
        "/?search=value",
        headers={"X-Request-ID": "request-1", "X-Forwarded-For": "192.0.2.1"},
    )

    assert response.status_code == 200
    assert len(records) == 1
    assert "method=GET" in records[0]
    assert "path=/" in records[0]
    assert "request_id=request-1" in records[0]
