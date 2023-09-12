import pytest
from nldcsc.http_apis.base_class.api_base_class import ApiBaseClass


class HttpApi(ApiBaseClass):
    def __init__(self, baseurl: str, **kwargs):
        super().__init__(baseurl, **kwargs)


@pytest.fixture
def http_api():
    ha = HttpApi(baseurl="http://localhost:8000", user_agent="HTTP_API", api_path="api")

    yield ha


class TestHttpApis:
    def test_headers(self, http_api):

        assert http_api.headers == {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "HTTP_API",
        }

        http_api.set_header_field("Testing", "Custom header")

        assert http_api.headers["Testing"] == "Custom header"

        http_api.del_header_field("Testing")

        assert http_api.headers == {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "HTTP_API",
        }

        http_api.clear_headers()

        assert http_api.headers is None

        http_api.reset_headers()

        assert http_api.headers == {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "HTTP_API",
        }

    def test_paths(self, http_api):

        assert http_api.baseurl == "http://localhost:8000"

        assert http_api.api_path == "api"
