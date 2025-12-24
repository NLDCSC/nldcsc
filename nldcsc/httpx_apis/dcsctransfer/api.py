import asyncio
from collections import defaultdict
from collections.abc import Callable
from functools import partial, wraps
import math
import os
from typing import IO, Any, TypeVar, ParamSpec, Awaitable
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

    def _upload_files(
        self, *handles: IO[bytes] | AsyncTextIOWrapper, upload_info: dict
    ):
        max_chunk_size = upload_info["max_chunk_size"]
        batch: dict = yield [os.path.basename(io.name) for io in handles]

        batch_id = batch["batch_id"]
        chunks = defaultdict(list)

        for chunk in batch["expected"]:
            chunks[chunk["file"]].append(chunk["chunk_id"])

        file_size, handle = yield chunks

        while any(chunks.values()):
            file_size, handle = (
                yield batch_id,
                chunks[os.path.basename(handle.name)].pop(),
                max_chunk_size,
                math.ceil(file_size / max_chunk_size),
                os.path.basename(handle.name),
            )

    async def a_upload_files(
        self,
        *file_handles: AsyncTextIOWrapper,
        comment: str = None,
        is_malware: bool = True,
    ):
        helper = self._upload_files(
            *file_handles, upload_info=await self.a_get_upload_info()
        )
        helper.send(await self.a_request_batch(next(helper), comment, is_malware))

        async def upload(file_handle: AsyncTextIOWrapper):
            await file_handle.seek(0, os.SEEK_END)
            file_size = await file_handle.tell()
            await file_handle.seek(0, os.SEEK_SET)

            batch_id, chunk_id, chunk_size, chunk_count, filename = helper.send(
                (file_size, file_handle)
            )

            for idx in range(chunk_count):
                result = await self.a_upload_chunk(
                    batch_id,
                    chunk_id,
                    idx,
                    chunk_count,
                    filename,
                    await file_handle.read(chunk_size),
                )

            return {**result, "file": filename}

        return await asyncio.gather(
            *(upload(file_handle) for file_handle in file_handles)
        )

    def upload_files(
        self, *file_handles: IO[bytes], comment: str = None, is_malware: bool = True
    ):
        helper = self._upload_files(*file_handles, upload_info=self.get_upload_info())
        helper.send(self.request_batch(next(helper), comment, is_malware))

        results = []

        for file_handle in file_handles:
            file_handle.seek(0, os.SEEK_END)
            file_size = file_handle.tell()

            file_handle.seek(0, os.SEEK_SET)

            batch_id, chunk_id, chunk_size, chunk_count, filename = helper.send(
                (file_size, file_handle)
            )

            for idx in range(chunk_count):
                result = self.upload_chunk(
                    batch_id,
                    chunk_id,
                    idx,
                    chunk_count,
                    filename,
                    file_handle.read(chunk_size),
                )

            results.append({**result, "file": filename})
        return results
