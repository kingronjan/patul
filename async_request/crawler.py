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

    def __init__(self, reqs=None,
                 result_back=None,
                 error_back=None,
                 handle_cookies=True,
                 download_delay=0,
                 concurrent_requests=10,
                 max_retries=3,
                 priority=1,
                 event_loop=None,
                 queuesize=0):
        '''
        :param reqs: Request list
        :param result_back: function to process the result
        :param error_back: callback when error happen
        :param handle_cookies: handle the cookies or not
        :param download_delay: delayed time before download
        :param concurrent_requests: max concurrent requests
        :param priority: -1: first in first out, breadth-first
                          1: last in first out, depth-first
        :param event_loop: async event loop
        '''
        if priority == -1:
            self._queue = asyncio.Queue(queuesize)
        elif priority == 1:
            self._queue = asyncio.LifoQueue(queuesize)
        else:
            raise ValueError('Argument priority expect 1 or -1, got {}'.format(priority))
        for req in reqs or []:
            self.add_request(req)
        if handle_cookies:
            self.session = requests.Session()
        else:
            self.session = requests
        self.result_back = result_back
        self.error_back = error_back
        self.download_delay = download_delay
        self.concurrent_requests = concurrent_requests
        self.max_retries = max_retries
        self._loop = event_loop or asyncio.get_event_loop()

    def add_request(self, request):
        try:
            self._queue.put_nowait(request)
        except asyncio.queues.QueueFull:
            async def add_request():
                await self._queue.put(request)
            self._loop.create_task(add_request())

    def next_request(self):
        return self._queue.get_nowait()

    def process_exception(self, e, request):
        if self.error_back:
            self.process_output(self.error_back(e, request))
        elif isinstance(e, (ConnectionError, Timeout)):
            self.retry(request)
        else:
            exc_type, exc_value, exc_traceback_obj = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback_obj, limit=3)

    def process_output(self, result):
        if result is None:
            return
        elif isinstance(result, Request):
            self.add_request(result)
        elif self.result_back:
            self.result_back(result)

    def retry(self, request):
        retry_times = request.meta.get('retry_times', 0)
        if 'max_retry_times' in request.meta:
            max_retries = request.meta['max_retry_times']
        else:
            max_retries = self.max_retries
        if retry_times < max_retries:
            retry_times += 1
            request.meta['retry_times'] = retry_times
            logger.debug('Prepare to retry {}'.format(request))
            self.add_request(request)
        else:
            logger.debug('Gave up retry {}'.format(request))

    def download(self, request):
        logger.debug('Requesting {}'.format(request))
        try:
            response = self.session.request(**request.request_kwargs)
        except Exception as e:
            return self.process_exception(e, request)
        response = Response(response, request)
        logger.debug('Requested {}'.format(response))
        return response

    async def crawl(self, request):
        await asyncio.sleep(self.download_delay)
        response = await self._loop.run_in_executor(None, self.download, request)
        if not response:
            return
        results = request.callback(response)
        if results is None:
            return
        try:
            results = iter(results)
        except TypeError:
            logger.warning('Except an iterable object, got {}'.format(type(results)))
        else:
            for x in results:
                self.process_output(x)

    async def start_crawl(self):
        def iter_task():
            try:
                for i in range(self.concurrent_requests):
                    yield self.crawl(self.next_request())
            except asyncio.queues.QueueEmpty:
                return
        await asyncio.gather(*iter_task())

    def run(self):
        while self._queue.qsize():
            self._loop.run_until_complete(self.start_crawl())

    def close(self):
        if isinstance(self.session, requests.Session):
            self.session.close()
        self._loop.close()

    def __del__(self):
        self.close()
