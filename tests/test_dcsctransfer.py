import asyncio
import io
from unittest.mock import AsyncMock, Mock

import httpx
import pytest

from nldcsc.httpx_apis.dcsctransfer.api import (
    DCSCTransferAPI,
    UploadHelper,
    async_call,
    json_parser,
)


class NamedBytesIO(io.BytesIO):
    def __init__(self, name, value):
        super().__init__(value)
        self.name = name


def test_upload_helper_prepares_batches_and_tracks_chunks():
    helper = UploadHelper({"max_chunk_size": 4})
    handle = NamedBytesIO("/tmp/report.bin", b"data")
    assert helper.prepare_batch(handles=[handle], filenames=["extra.bin"]) == [
        "extra.bin",
        "report.bin",
    ]
    with pytest.raises(KeyError):
        helper.get_from_batch(filename="report.bin")

    helper.set_batch(
        {
            "batch_id": "batch-1",
            "expected": [
                {"file": "report.bin", "chunk_id": "part-1"},
                {"file": "extra.bin", "chunk_id": "part-2"},
            ],
        }
    )
    assert helper.batch_id == "batch-1"
    assert helper.get_from_batch(handle=handle) == ("part-1", "report.bin")
    assert helper.get_from_batch(filename="extra.bin") == ("part-2", "extra.bin")
    assert helper.calculate_chunk_count(0) == -1
    assert helper.calculate_chunk_count(4) == 1
    assert helper.calculate_chunk_count(5) == 2
    assert helper.should_finalize(-1) is True
    with pytest.raises(EOFError):
        helper.get_from_batch(filename="report.bin")


def test_sync_transfer_methods_parse_responses_and_upload_chunks():
    api = DCSCTransferAPI(
        "https://transfer.test", "token", use_async_client=False
    )

    def response(data):
        return httpx.Response(200, json=data)

    api.call = Mock(
        side_effect=[
            response({"id": "file"}),
            response({"id": "md5"}),
            response({"files": ["a"]}),
            response({"max_chunk_size": 4}),
            response({"batch_id": "batch"}),
            response({"uploaded": True}),
            response({"finalized": True}),
        ]
    )

    assert api.get_file("file-id") == {"id": "file"}
    assert api.search_md5("hash") == {"id": "md5"}
    assert api.list_hashes(start=2, size=1) == {"files": ["a"]}
    assert api.get_upload_info() == {"max_chunk_size": 4}
    assert api.request_batch(["a.bin"], comment="sample") == {"batch_id": "batch"}
    assert api.upload_chunk("batch", "chunk", 0, 1, "a.bin", b"data") == {
        "uploaded": True
    }
    assert api.finalize_chunk("batch", "chunk", 1) == {"finalized": True}
    assert api.call.call_args_list[1].kwargs["resources"] == "hashes/md5/hash"
    assert api.call.call_args_list[5].kwargs["files"]["content"] == (
        "a.bin",
        b"data",
        "application/octet-stream",
    )


def test_sync_transfer_paginates_hashes_and_uploads_files():
    api = DCSCTransferAPI(
        "https://transfer.test", "token", use_async_client=False
    )
    api.list_hashes = Mock(
        side_effect=[
            {"files": ["a", "b"], "start": 0, "size": 2},
            {"files": ["c"], "start": 2, "size": 2},
        ]
    )
    assert list(api.iter_hashes(fetch_size=2)) == ["a", "b", "c"]
    assert [call.args for call in api.list_hashes.call_args_list] == [(0, 2), (2, 2)]

    api.get_upload_info = Mock(return_value={"max_chunk_size": 4})
    api.request_batch = Mock(
        return_value={
            "batch_id": "batch",
            "expected": [{"file": "report.bin", "chunk_id": "chunk"}],
        }
    )
    api.upload_chunk = Mock(return_value={"uploaded": True})
    result = api.upload_files(
        NamedBytesIO("/tmp/report.bin", b"123456"), comment="scan"
    )

    assert result == [{"uploaded": True, "file": "report.bin"}]
    assert api.upload_chunk.call_count == 2
    assert api.upload_chunk.call_args_list[0].args[-1] == b"1234"
    assert api.upload_chunk.call_args_list[1].args[-1] == b"56"


def test_async_transfer_methods_and_hash_iteration():
    api = DCSCTransferAPI("https://transfer.test", "token")

    def response(data):
        return httpx.Response(200, json=data)

    api.a_call = AsyncMock(
        side_effect=[
            response({"id": "file"}),
            response({"id": "sha1"}),
            response({"files": ["a", "b"], "start": 0, "size": 2}),
            response({"files": ["c"], "start": 2, "size": 2}),
        ]
    )

    async def run():
        file_data = await api.a_get_file("file-id")
        sha_data = await api.a_search_sha1("hash")
        files = [item async for item in api.a_iter_hashes(fetch_size=2)]
        return file_data, sha_data, files

    assert asyncio.run(run()) == ({"id": "file"}, {"id": "sha1"}, ["a", "b", "c"])
    assert api.a_call.call_args_list[1].kwargs["resources"] == "hashes/sha1/hash"


def test_transfer_methods_reject_wrong_client_mode_and_parse_errors():
    async_api = DCSCTransferAPI("https://transfer.test", "token")
    sync_api = DCSCTransferAPI(
        "https://transfer.test", "token", use_async_client=False
    )

    with pytest.raises(AttributeError, match="async method whilst using a sync client"):
        asyncio.run(sync_api.a_get_file("id"))
    with pytest.raises(AttributeError, match="sync method whilst using a async client"):
        async_api.get_file("id")

    response = httpx.Response(200, json={"ok": True})
    assert json_parser(response) == {"ok": True}
