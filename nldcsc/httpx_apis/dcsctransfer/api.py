import asyncio
from collections import defaultdict
from collections.abc import Callable
from functools import partial, wraps
import math
import os
from typing import (
    IO,
    Any,
    DefaultDict,
    Iterable,
    TypeVar,
    ParamSpec,
    Awaitable,
)
from aiofiles.threadpool.text import AsyncTextIOWrapper

from httpx import Response
from nldcsc.httpx_apis.base_class.httpx_base_class import HttpxBaseClass

T = TypeVar("T")
P = ParamSpec("P")


def signature_of(_: Callable[P, Any]) -> Callable[[Callable[..., T]], Callable[P, T]]:
    def wrapper(wrapped: Callable[..., T]) -> Callable[P, T]:
        return wrapped

    return wrapper


def async_call(
    calls: Callable[P, Any], parser: Callable[[Response | str | Any], T] = None
) -> Callable[[Callable[..., Any]], Callable[P, Awaitable[Response | str | Any | T]]]:
    def wrapper(
        _: Callable[..., Any],
    ) -> Callable[P, Awaitable[Response | str | Any | T]]:
        @wraps(calls)
        async def inner(
            self: "DCSCTransferAPI", *args, **kwargs
        ) -> Awaitable[Response | str | Any]:
            if not self.use_async_client:
                raise AttributeError(
                    "You are attempting to call a async method whilst using a sync client!"
                )

            args, kwargs = calls(self, *args, **kwargs)

            r = await self.a_call(*args, **kwargs)

            return parser(r) if parser else r

        return inner

    return wrapper


def sync_call(
    calls: Callable[P, Any], parser: Callable[[Response | str | Any], T] = None
) -> Callable[[Callable[..., Any]], Callable[P, Response | str | Any | T]]:
    def wrapper(_: Callable[..., Any]) -> Callable[P, Response | str | Any | T]:
        @wraps(calls)
        def inner(self: "DCSCTransferAPI", *args, **kwargs) -> Response | str | Any | T:
            if self.use_async_client:
                raise AttributeError(
                    "You are attempting to call a sync method whilst using a async client!"
                )

            args, kwargs = calls(self, *args, **kwargs)

            r = self.call(*args, **kwargs)

            return parser(r) if parser else r

        return inner

    return wrapper


def json_parser(response: Response) -> dict[Any, Any]:
    return response.json()


class UploadHelper:
    def __init__(self, upload_info: dict):
        self.max_chunk_size: int = upload_info["max_chunk_size"]
        self.batch_id: str = None
        self.chunks: DefaultDict[str, list[str]] = None

    def prepare_batch(
        self,
        *,
        handles: Iterable[IO[bytes] | AsyncTextIOWrapper] = None,
        filenames: list[str] = None,
    ):
        if not filenames:
            filenames = []

        if handles:
            filenames.extend(os.path.basename(io.name) for io in handles)

        return filenames

    def set_batch(self, batch: dict):
        self.batch_id = batch["batch_id"]
        self.chunks = defaultdict(list)

        for chunk in batch["expected"]:
            self.chunks[chunk["file"]].append(chunk["chunk_id"])

    def get_from_batch(
        self, *, handle: IO[bytes] | AsyncTextIOWrapper = None, filename: str = None
    ):
        if not self.batch_id:
            raise KeyError

        if not any(self.chunks.values()):
            raise EOFError

        filename = os.path.basename(handle.name) if handle else filename

        return self.chunks[filename].pop(), filename

    def calculate_chunk_count(self, file_size: int):
        return math.ceil(file_size / self.max_chunk_size)


class DCSCTransferAPI(HttpxBaseClass):
    def __init__(
        self,
        baseurl,
        token,
        api_path="api",
        proxies=None,
        user_agent="HttpxBaseClass",
        use_async_client=True,
        **kwargs,
    ):
        super().__init__(
            baseurl, api_path, proxies, user_agent, use_async_client, **kwargs
        )

        self.myheaders = self.__default_headers
        self.set_header_field("Access-Token", token)

    @property
    def __default_headers(self) -> dict:
        """
        Property to return the default headers
        """
        # print("call")
        return {
            "Accept": "application/json",
            "User-Agent": f"{self.user_agent}",
        }

    def _get_file(self, uuid: str):
        """
        Gets a file by uuid
        """

        resource = f"files/{uuid}"

        return (self.methods.GET,), {"resources": resource}

    def _get_upload_info(self):
        resource = "uploads/info"

        return (self.methods.GET,), {"resources": resource}

    def _search_hash(self, hash: str, hash_type: str):
        resource = f"hashes/{hash_type}/{hash}"

        return (self.methods.GET,), {"resources": resource}

    def _search_hash_sign(self, hash: str): ...

    def _list_hashes(self, start: int = 0, size: int = 10):
        resource = "hashes/list"

        data = {"start": start, "size": size}

        return (self.methods.GET,), {"resources": resource, "params": data}

    def _iter_hashes(self, data: dict):
        def parse(data: dict):
            size = data.get("size", 10)
            start = data.get("start", 0)

            return data.get("files", []), start + size, size

        files, next, size = parse(data)

        while len(files) == size:
            data = yield files, next

            files, next, size = parse(data)

        yield files, None

    def _get_upload_info(self):
        resource = "uploads/info"

        return (self.methods.GET,), {"resources": resource}

    def _request_batch(
        self, files: list[str], comment: str = None, is_malware: bool = True
    ):
        resource = "uploads/parts"

        data = {"is_malware": is_malware, "files": files}

        if comment:
            data["comment"] = comment

        return (self.methods.POST,), {"resources": resource, "json": data}

    def _upload_chunk(
        self,
        batch_id: str,
        chunk_id: str,
        chunk_idx: int,
        chunk_count: int,
        filename: str,
        content: bytes,
    ):
        resource = "uploads/parts"

        data = {
            "batch_id": batch_id,
            "chunk_id": chunk_id,
            "chunk_idx": chunk_idx,
            "chunk_count": chunk_count,
        }

        files = {"content": (filename, content, "application/octet-stream")}

        return (self.methods.PUT,), {
            "resources": resource,
            "data": data,
            "files": files,
        }

    @signature_of(_get_file)
    @async_call(_get_file, json_parser)
    async def a_get_file(self): ...

    @signature_of(_get_file)
    @sync_call(_get_file, json_parser)
    def get_file(self): ...

    @signature_of(_search_hash_sign)
    @async_call(partial(_search_hash, hash_type="md5"), json_parser)
    async def a_search_md5(self): ...

    @signature_of(_search_hash_sign)
    @sync_call(partial(_search_hash, hash_type="md5"), json_parser)
    def search_md5(self): ...

    @signature_of(_search_hash_sign)
    @async_call(partial(_search_hash, hash_type="sha1"), json_parser)
    async def a_search_sha1(self): ...

    @signature_of(_search_hash_sign)
    @sync_call(partial(_search_hash, hash_type="sha1"), json_parser)
    def search_sha1(self): ...

    @signature_of(_search_hash_sign)
    @async_call(partial(_search_hash, hash_type="sha256"), json_parser)
    async def a_search_sha256(self): ...

    @signature_of(_search_hash_sign)
    @sync_call(partial(_search_hash, hash_type="sha256"), json_parser)
    def search_sha256(self): ...

    @signature_of(_list_hashes)
    @async_call(_list_hashes, json_parser)
    async def a_list_hashes(self): ...

    @signature_of(_list_hashes)
    @sync_call(_list_hashes, json_parser)
    def list_hashes(self): ...

    @signature_of(_get_upload_info)
    @async_call(_get_upload_info, json_parser)
    async def a_get_upload_info(self): ...

    @signature_of(_get_upload_info)
    @sync_call(_get_upload_info, json_parser)
    def get_upload_info(self): ...

    @signature_of(_request_batch)
    @async_call(_request_batch, json_parser)
    async def a_request_batch(self): ...

    @signature_of(_request_batch)
    @sync_call(_request_batch, json_parser)
    def request_batch(self): ...

    @signature_of(_upload_chunk)
    @async_call(_upload_chunk, json_parser)
    async def a_upload_chunk(self): ...

    @signature_of(_upload_chunk)
    @sync_call(_upload_chunk, json_parser)
    def upload_chunk(self): ...

    def iter_hashes(self, fetch_size: int = 10):
        generator = self._iter_hashes(self.list_hashes(0, fetch_size))

        files, start = next(generator)

        while True:
            yield from files

            if start is None:
                break

            files, start = generator.send(self.list_hashes(start, fetch_size))

    async def a_iter_hashes(self, fetch_size: int = 10):
        generator = self._iter_hashes(await self.a_list_hashes(0, fetch_size))

        files, start = next(generator)

        while True:
            for file in files:
                yield file

            if start is None:
                break

            files, start = generator.send(await self.a_list_hashes(start, fetch_size))

    async def a_upload_files(
        self,
        *file_handles: AsyncTextIOWrapper,
        comment: str = None,
        is_malware: bool = True,
    ):
        helper = UploadHelper(await self.a_get_upload_info())
        helper.set_batch(
            await self.a_request_batch(
                helper.prepare_batch(handles=file_handles), comment, is_malware
            )
        )

        async def upload(file_handle: AsyncTextIOWrapper):
            await file_handle.seek(0, os.SEEK_END)
            file_size = await file_handle.tell()
            await file_handle.seek(0, os.SEEK_SET)

            chunk_id, filename = helper.get_from_batch(handle=file_handle)
            chunk_count = helper.calculate_chunk_count(file_size)

            for idx in range(chunk_count):
                result = await self.a_upload_chunk(
                    helper.batch_id,
                    chunk_id,
                    idx,
                    chunk_count,
                    filename,
                    await file_handle.read(helper.max_chunk_size),
                )

            return {**result, "file": filename}

        return await asyncio.gather(
            *(upload(file_handle) for file_handle in file_handles)
        )

    def upload_files(
        self, *file_handles: IO[bytes], comment: str = None, is_malware: bool = True
    ):
        helper = UploadHelper(self.get_upload_info())
        helper.set_batch(
            self.request_batch(
                helper.prepare_batch(handles=file_handles), comment, is_malware
            )
        )

        results = []

        for file_handle in file_handles:
            file_handle.seek(0, os.SEEK_END)
            file_size = file_handle.tell()

            file_handle.seek(0, os.SEEK_SET)

            chunk_id, filename = helper.get_from_batch(handle=file_handle)
            chunk_count = helper.calculate_chunk_count(file_size)

            for idx in range(chunk_count):
                result = self.upload_chunk(
                    helper.batch_id,
                    chunk_id,
                    idx,
                    chunk_count,
                    filename,
                    file_handle.read(helper.max_chunk_size),
                )

            results.append({**result, "file": filename})
        return results
