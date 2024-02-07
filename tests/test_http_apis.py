import pytest
import requests
import requests_mock

from nldcsc.http_apis.base_class.api_base_class import ApiBaseClass


class HttpApi(ApiBaseClass):
    def __init__(self, baseurl: str, **kwargs):
        super().__init__(baseurl, **kwargs)

    def get_dummy_endpoint(self):
        resource = "dummy"

        return self.call(self.methods.GET, resource=resource)

    def get_dummy_endpoint_url_param(self, data=None):
        resource = "dummy"

        return self.call(self.methods.GET, resource=resource, data=data)

    def get_dummy_response_endpoint(self):
        resource = "dummy"
        data = {"data": "data"}

        return self.call(
            self.methods.GET, resource=resource, return_response_object=True, data=data
        )

    def post_str_dummy(self):
        resource = "dummy"
        data = "data"

        return self.call(self.methods.POST, resource=resource, data=data)

    def put_str_dummy(self):
        resource = "dummy"
        data = "data"

        return self.call(self.methods.PUT, resource=resource, data=data)

    def patch_dict_dummy(self):
        resource = "dummy"
        data = {"data": "data"}

        return self.call(self.methods.PATCH, resource=resource, data=data)

    def delete_dict_dummy(self):
        resource = "dummy"

        return self.call(self.methods.DELETE, resource=resource)

    def post_invalid_data_dummy(self):
        resource = "dummy"
        data = 1

        return self.call(self.methods.POST, resource=resource, data=data)

    def post_unserializable_data_dummy(self):
        class DummyClass:
            pass

        resource = "dummy"
        data = {"data": DummyClass()}

        return self.call(self.methods.POST, resource=resource, data=data)


@pytest.fixture
def http_api():
    ha = HttpApi(baseurl="http://localhost:8000", user_agent="HTTP_API")

    yield ha


@pytest.fixture
def http_path_api():
    ha = HttpApi(
        baseurl="http://localhost:8000",
        user_agent="HTTP_API",
        api_path="api",
        verify=True,
    )

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

    def test_paths(self, http_path_api, http_api):
        assert http_path_api.baseurl == "http://localhost:8000"

        assert http_path_api.api_path == "api"

        assert (
            http_path_api._build_url("resource") == "http://localhost:8000/api/resource"
        )

        assert http_api._build_url("resource") == "http://localhost:8000/resource"

    def test_dummy_calls(self, http_api):
        with pytest.raises(requests.ConnectionError):
            http_api.get_dummy_endpoint()

        with pytest.raises(requests.ConnectionError):
            http_api.get_dummy_endpoint_url_param()

        with pytest.raises(requests.ConnectionError):
            http_api.post_str_dummy()

        with pytest.raises(requests.ConnectionError):
            http_api.put_str_dummy()

        with pytest.raises(requests.ConnectionError):
            http_api.patch_dict_dummy()

        with pytest.raises(requests.ConnectionError):
            http_api.delete_dict_dummy()

    def test_session_calls(self, http_api):
        with requests_mock.Mocker() as m:
            m.get(
                "http://localhost:8000/dummy", text='{"data": "data"}', status_code=404
            )

            with pytest.raises(requests.ConnectionError):
                d = http_api.get_dummy_endpoint()

                assert d == {"data": "data"}

        with requests_mock.Mocker() as m:
            m.get(
                "http://localhost:8000/dummy?id=1&id2=10",
                json={"id": "1", "id2": 10, "result": "success"},
                status_code=200,
            )

            d = http_api.get_dummy_endpoint_url_param(data={"id": 1, "id2": 10})

            assert d == {"id": "1", "id2": 10, "result": "success"}

        with requests_mock.Mocker() as m:
            m.get(
                "http://localhost:8000/dummy", text='{"data": "data"}', status_code=200
            )

            d = http_api.get_dummy_endpoint_url_param()

            assert d == {"data": "data"}

        with requests_mock.Mocker() as m:
            m.get(
                "http://localhost:8000/dummy", text='{"data": "data"}', status_code=200
            )

            d = http_api.get_dummy_response_endpoint()

            assert isinstance(d, requests.Response)

        with requests_mock.Mocker() as m:
            m.get(
                "http://localhost:8000/dummy",
                text="just string data",
                status_code=200,
                headers={"content-type": "text-plain"},
            )

            d = http_api.get_dummy_endpoint()

            assert isinstance(d, requests.Response)

        with requests_mock.Mocker() as m:
            m.get(
                "http://localhost:8000/dummy",
                text="just string data",
                status_code=200,
                headers={"content-type": "text/plain"},
            )

            d = http_api.get_dummy_endpoint()

            assert isinstance(d, str)
            assert d == "just string data"

        with requests_mock.Mocker() as m:
            m.get(
                "http://localhost:8000/dummy",
                text="just string data",
                status_code=200,
            )

            http_api.get_dummy_endpoint()
        with pytest.raises(requests.ConnectionError):
            http_api.delete_dict_dummy()

        with requests_mock.Mocker() as m:
            m.post(
                "http://localhost:8000/dummy",
                text="just string data",
                status_code=200,
            )

            with pytest.raises(TypeError):
                http_api.post_invalid_data_dummy()

        with requests_mock.Mocker() as m:
            m.post(
                "http://localhost:8000/dummy",
                text="just string data",
                status_code=200,
            )

            with pytest.raises(TypeError):
                http_api.post_unserializable_data_dummy()
