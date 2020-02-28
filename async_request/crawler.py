# coding=utf-8

import asyncio
import functools

import requests as _requests
from requests.exceptions import ConnectionError, Timeout

from async_request.request import Request
from async_request.response import Response
from async_request.utils import iter_results, get_logger


def _run_in_executor(func):
    @functools.wraps(func)
    def wrapped(crawler, *args):
        return crawler.loop.run_in_executor(None, func, crawler, *args)
    return wrapped


class Crawler(object):

    def __init__(self,
                 requests=None,
                 result_back=None,
                 handle_cookies=True,
                 download_delay=0,
                 concurrent_requests=10,
                 max_retries=3,
                 priority=1,
                 event_loop=None,
                 log_level='DEBUG',
                 log_file=None):
        """
        :param requests: Request list
        :param result_back: function to process the result
        :param handle_cookies: handle the cookies or not
        :param download_delay: delayed time before download
        :param concurrent_requests: max concurrent requests
        :param priority: -1: first in first out, breadth-first
                          1: last in first out, depth-first
        :param event_loop: async event loop
        :param log_level: logs level
        :param log_file: if not None, logs will save to it
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
        for request in requests or []:
            self.add_request(request)
        self.result_back = result_back
        self.download_delay = download_delay
        self.concurrent_requests = concurrent_requests
        self.max_retries = max_retries
        self.loop = event_loop or asyncio.get_event_loop()
        self.logger = get_logger('asyncrequest.Crawler', level=log_level, file_path=log_file)

    def add_request(self, request):
        self._queue.put_nowait(request)

    async def _add_request(self, request):
        await self._queue.put(request)

    @_run_in_executor
    def download(self, request):
        retries = request.meta.get('retry_times')
        if retries:
            self.logger.debug(f'Retrying download: {request} (retried {retries-1} times)')
        try:
            r = self.session.request(**request.requests_kwargs())
        except Exception as e:
            if isinstance(e, (ConnectionError, Timeout,)):
                self.retry_request(request)
            return self.logger.exception(e)
        response = Response(r, request)
        self.logger.debug(f'Downloaded: {response!r}')
        return response

    def retry_request(self, request, max_retries=None):
        if max_retries is None:
            max_retries = self.max_retries
        retries = request.meta.get('retry_times', 0)
        if retries < max_retries:
            request.meta['retry_times'] = retries + 1
            self.add_request(request)
        else:
            self.logger.debug(f'Gave up retry {request}')

    async def process_response(self, response, request):
        if not response:
            return
        if not request.callback:
            return self.logger.warning(f'No function to parse {request}')
        try:
            results = request.callback(response)
        except Exception as e:
            return self._log_parse_error(e, response)
        try:
            for result in iter_results(results):
                if isinstance(result, Request):
                    await self._add_request(result)
                else:
                    await self.process_result(result)
        except Exception as e:
            self._log_parse_error(e, response)

    def _log_parse_error(self, e, response):
        self.logger.error(f'Error happened when parsing: {response!r}, cause: {e}')
        self.logger.exception(e)

    @_run_in_executor
    def process_result(self, result):
        self.logger.debug(f'Crawled result: {result}')
        if not self.result_back:
            return
        try:
            self.result_back(result)
        except Exception as e:
            self.logger.error(f'Error happened when processing result: {result}, cause: {e}')
            self.logger.exception(e)

    async def crawl(self, request):
        await asyncio.sleep(self.download_delay)
        response = await self.download(request)
        await self.process_response(response, request)

    def _get_crawl_tasks(self):
        tasks = []
        try:
            for _ in range(self.concurrent_requests):
                request = self._queue.get_nowait()
                tasks.append(self.crawl(request))
        except asyncio.queues.QueueEmpty:
            pass
        return tasks

    async def _run(self):
        while self._queue.qsize():
            await asyncio.gather(*self._get_crawl_tasks())

    def run(self, close_after_crawled=True):
        self.loop.run_until_complete(self._run())
        self.close(close_after_crawled)

    def close(self, close_loop=True):
        if isinstance(self.session, _requests.Session):
            self.session.close()
        if close_loop:
            self.loop.close()

    def __del__(self):
        self.close()
