import asyncio
import concurrent.futures
import functools
import logging
from collections import Coroutine
from typing import Generator, AsyncGenerator

import requests as _requests
from requests.exceptions import ConnectionError, Timeout

from patul.request import Request
from patul.response import Response

LOG_FMT = '%(asctime)s [%(name)s] %(levelname)s %(message)s'
LOG_DATE_FMT = '%Y-%m-%d %H:%M:%S'


def _run_in_executor(func):
    @functools.wraps(func)
    def wrapped(crawler, *args):
        return crawler.loop.run_in_executor(crawler.executor, func, crawler, *args)
    return wrapped


class Crawler(object):

    def __init__(self,
                 start_requests=None,
                 result_back=None,
                 handle_cookies=True,
                 download_delay=0,
                 concurrent_requests=10,
                 max_retries=3,
                 priority=1,
                 log_settings=None,
                 loop=None):
        """
        :param result_back: function to process the result
        :param handle_cookies: handle the cookies or not
        :param download_delay: delayed time before download
        :param concurrent_requests: max concurrent requests
        :param priority: -1: first in first out, breadth-first
                          1: last in first out, depth-first
        :param log_settings: log settings
        :param loop: async event loop
        """
        if priority == -1:
            self._queue = asyncio.Queue()
        elif priority == 1:
            self._queue = asyncio.LifoQueue()
        else:
            raise ValueError(f'Argument priority expect 1 or -1, got {priority}')

        if handle_cookies:
            self.session = _requests.Session()
        else:
            self.session = _requests

        for request in start_requests or []:
            self.put_request(request)

        self.result_back = result_back
        self.download_delay = download_delay
        self.concurrent_requests = concurrent_requests
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.concurrent_requests)
        self.max_retries = max_retries
        self.loop = loop or asyncio.get_event_loop()
        self.logger = _logger(log_settings or {})

    def put_request(self, request):
        self._queue.put_nowait(request)

    def run(self, close_loop=True):
        self.loop.run_until_complete(self._run())
        self.close(close_loop)

    async def crawl(self, request):
        await asyncio.sleep(self.download_delay)
        response = await self.download(request)
        if response is not None:
            await self.process_response(response, request)

    async def _run(self):
        def iter_task():
            try:
                for _ in range(self.concurrent_requests):
                    request = self._queue.get_nowait()
                    yield self.crawl(request)
            except asyncio.queues.QueueEmpty:
                pass

        while self._queue.qsize():
            await asyncio.gather(*iter_task())

    def close(self, close_loop=True):
        if isinstance(self.session, _requests.Session):
            self.session.close()
        if close_loop:
            self.loop.close()
        self.executor.shutdown()

    @_run_in_executor
    def download(self, request):
        try:
            r = self.session.request(**request.requests_kwargs())
            return Response(r, request)
        except Exception as e:
            if isinstance(e, (ConnectionError, Timeout,)):
                self.loop.create_task(self.retry_download(request, e))
            else:
                self._log_err('downloading', request)

    async def retry_download(self, request, reason):
        retries = request.meta.get('retry_times', 0)
        if retries < self.max_retries:
            await self._queue.put(request)
            request.meta['retry_times'] = retries + 1
            self.logger.debug(
                f'Preparing to retry: {request} caused by {reason}. (retried {retries - 1} times)'
            )
        elif self.max_retries != 0:
            self.logger.debug(f'Gave up retry {request}')

    async def process_response(self, response, request):
        self.logger.debug(f'Downloaded: {response!r}')
        if not request.callback:
            return self.logger.warning(f'No function to parse {request}')
        try:
            outputs = request.callback(response)
            outputs = await coro_wrapper(outputs)
            await self.process_output(outputs)
        except:
            self._log_err('parsing', response)

    async def process_output(self, outputs):
        async for output in _iter_outputs(outputs):
            if output is None:
                continue
            if isinstance(output, Request):
                await self._queue.put(output)
            else:
                await self.process_result(output)

    async def process_result(self, result):
        self.logger.debug(f'Crawled result: {result}')
        if not self.result_back:
            return
        try:
            await coro_wrapper(self.result_back(result))
        except:
            self._log_err('processing result', result)

    def _log_err(self, situation, info):
        self.logger.error(f'Error happened when {situation}: {info}', exc_info=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


async def coro_wrapper(maybe_coro):
    if isinstance(maybe_coro, Coroutine):
        return await maybe_coro
    return maybe_coro


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


def _iter_outputs(outputs):
    if isinstance(outputs, AsyncGenerator):
        return outputs
    if outputs is None:
        outputs = []
    elif not isinstance(outputs, Generator):
        outputs = [outputs]
    return AsyncIteratorWrapper(outputs)


def _logger(settings):
    logger = logging.getLogger('patul.crawler')
    logger.setLevel(settings.get('level', 'DEBUG'))

    if 'formatter' in settings:
        formatter = settings['formatter']
    else:
        formatter = logging.Formatter(fmt=LOG_FMT, datefmt=LOG_DATE_FMT)

    if 'fp' in settings:
        handler = logging.FileHandler(settings['fp'], encoding='utf-8')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    if settings.get('to_stream', True):
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    return logger
