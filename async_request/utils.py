import hashlib
import logging
import weakref
from collections import Coroutine
from typing import Generator, AsyncGenerator


def md5fy_request(request):
    md5 = hashlib.md5()

    def update(obj):
        if not obj:
            return
        md5.update(str(obj).encode('utf-8'))

    update(request.url)
    update(request.params)
    update(request.method)
    if request.method == 'POST':
        update(request.json)
        update(request.data)
    return md5.hexdigest()


async def coro_wrapper(maybe_coro):
    if isinstance(maybe_coro, Coroutine):
        return await maybe_coro
    return maybe_coro


def iter_outputs(outputs):
    if isinstance(outputs, AsyncGenerator):
        return outputs
    if outputs is None:
        outputs = []
    elif not isinstance(outputs, Generator):
        outputs = [outputs]
    return AsyncIteratorWrapper(outputs)


class AsyncIteratorWrapper:

    def __init__(self, obj):
        self._it = iter(obj)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self._it)
        except StopIteration:
            raise StopAsyncIteration


_handlers = weakref.WeakValueDictionary()

def get_logger(name, level='DEBUG', file_path=None):
    """
    return logger.

    :param file_path:
        if is not None, logs will save to it,
        else, logs will not save to file.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    formatter = logging.Formatter(
        fmt='%(asctime)s [%(name)s] %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    if not 'stream' in _handlers:
        stream = logging.StreamHandler()
        stream.setFormatter(formatter)
        _handlers['stream'] = stream
    logger.addHandler(_handlers['stream'])

    if file_path is not None:
        if not 'file' in _handlers:
            file = logging.FileHandler(filename=file_path, encoding='utf-8')
            file.setFormatter(formatter)
            _handlers['file'] = file
        logger.addHandler(_handlers['file'])

    return logger
