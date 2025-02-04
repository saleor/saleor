from gzip import _WriteBufferStream  # type: ignore[attr-defined]


def __del_tmp__(self):
    del self.gzip_file


def patch_gzip():
    """Patch `__del__` in `_WriteBufferStream` from `gzip` to avoid memory leaks.

    Those changes will remove the circular references in `GzipFile`,  allowing memory to be freed immediately,
    without the need of a deep garbage collection cycle.
    Cycle: `GzipFile._buffer` -> `BufferedWriter._raw` -> `_WriteBufferStream.gzip_file` -> `GzipFile`.
    Issue: https://github.com/python/cpython/issues/129640
    """
    _WriteBufferStream.__del__ = __del_tmp__
