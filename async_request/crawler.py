# coding=utf-8

import asyncio
import logging
import sys
import traceback

import requests
from requests.exceptions import ConnectionError, Timeout

from async_request.request import Request
from async_request.response import Response

logger = logging.getLogger('async_request.Crawler')


class Crawler(object):
    '''
    @reqs
        list of instance of Request
        type: list
    @result_back
        callback when result came out
        accept argument: result
    @error_back
        callback when errors
        accept arguments: exception, request
    @handle_cookies
        if it's True (default is True)
        crawler will use requests.Session to handle cookies
    @download_delay
        delayed time before download
    @concurrent_requests
        max concurrent requests
        type: int
    @max_retries
        max_retries
        type: int
    @priority
        -1: first in first out, breadth-first
         1: last in first out, depth-first
    @event_loop
        async event loop
    '''
    def __init__(
            self,
            reqs=None,
            result_back=None,
            error_back=None,
            handle_cookies=True,
            download_delay=0,
            concurrent_requests=10,
            max_retries=3,
            priority=1,
            event_loop=None
        ):
        if priority == -1:
            self._request_queue = asyncio.Queue()
        elif priority == 1:
            self._request_queue = asyncio.LifoQueue()
        else:
            raise ValueError(f'Argument priority expect 1 or -1, got {priority}')
        if handle_cookies:
            self.session = requests.Session()
        else:
            self.session = requests
        self.result_back = result_back
        self.error_back = error_back
        self.download_delay = download_delay
        self.concurrent_requests = concurrent_requests
        self.max_retries = max_retries
        self.loop = event_loop or asyncio.get_event_loop()
        for req in reqs or []:
            self.add_request(req)

    def add_request(self, request):
        self._request_queue.put_nowait(request)

    def next_request(self):
        try:
            return self._request_queue.get_nowait()
        except asyncio.queues.QueueEmpty:
            return None

    def process_exception(self, e, request):
        if self.error_back:
            self.process_output(self.error_back(e, request))
        elif isinstance(e, (ConnectionError, Timeout)):
            self.retry(request)
        else:
            exc_type, exc_value, exc_traceback_obj = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback_obj, limit=3)

    async def process_output(self, result):
        if result is None:
            return
        elif isinstance(result, Request):
            self.add_request(result)
        elif self.result_back:
            await self.loop.run_in_executor(None, self.result_back, result)

    def retry(self, request):
        retry_times = request.meta.get('retry_times', 0)
        if 'max_retry_times' in request.meta:
            max_retries = request.meta['max_retry_times']
        else:
            max_retries = self.max_retries
        if retry_times < max_retries:
            retry_times += 1
            request.meta['retry_times'] = retry_times
            self.add_request(request)
        else:
            logger.debug('Gave up retry {}'.format(request))

    def download(self, request):
        try:
            response = self.session.request(**request.request_kwargs)
        except Exception as e:
            return self.process_exception(e, request)
        response = Response(response, request)
        logger.debug(f'Requested {response}')
        return response

    async def crawl(self, request):
        loop = asyncio.get_running_loop()
        await asyncio.sleep(self.download_delay)
        response = await loop.run_in_executor(None, self.download, request)
        if not response:
            return
        results = request.callback(response)
        if results is None:
            return
        try:
            results = iter(results)
        except TypeError:
            logger.warning(f'Except an iterable object, got {type(results)}')
        else:
            for x in results:
                await self.process_output(x)

    async def _run(self):

        def iter_task():
            for i in range(self.concurrent_requests):
                req = self.next_request()
                if req is None:
                    break
                yield self.crawl(req)

        while self._request_queue.qsize():
            await asyncio.gather(*iter_task())

    def run(self):
        self.loop.run_until_complete(self._run())

    def close(self):
        if isinstance(self.session, requests.Session):
            self.session.close()
        self.loop.close()

    def __del__(self):
        self.close()
