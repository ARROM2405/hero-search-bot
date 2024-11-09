from typing import IO, TypedDict


class DataDict(TypedDict, total=False):
    text: str
    chat_id: int
    reply_markup: str


class FilesDict(TypedDict):
    document: IO[bytes]


class ResponsePayload(TypedDict, total=False):
    data: DataDict
    files: FilesDict
