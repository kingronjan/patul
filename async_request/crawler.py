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
                 priority=1,
                 event_loop=None):
        '''
        :param reqs: Request list
        :param result_back: function to process the result
        :param error_back: callback when error happen
        :param handle_cookies: handle the cookies or not
        :param download_delay: delayed time before download
        :param concurrent_requests: max concurrent requests
        :param priority: -1: first in first out
                          1: last in first out
        :param event_loop: async event loop
        '''
        if priority == -1:
            self.request_queue = asyncio.Queue()
        elif priority == 1:
            self.request_queue = asyncio.LifoQueue()
        else:
            raise ValueError('Argument priority expect 1 or -1, got {}'.format(priority))
        for req in reqs or []:
            self.request_queue.put_nowait(req)
        if handle_cookies:
            self.session = requests.Session()
        else:
            self.session = requests
        self.result_back = result_back
        self.error_back = error_back
        self.download_delay = download_delay
        self.concurrent_requests = concurrent_requests
        self.event_loop = event_loop or asyncio.get_event_loop()

    def add_request(self, request):
        self.request_queue.put_nowait(request)

    def next_request(self):
        return self.request_queue.get_nowait()

    def process_exception(self, e, request):
        if self.error_back:
            self.process_output(self.error_back(e, request))
        if isinstance(e, (ConnectionError, Timeout)):
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
        if request.retry_times >= 0:
            logger.debug('Retrying %s' % request.url)
            request.retry_times -= 1
            self.add_request(request)
        else:
            logger.debug('Gave up retry {}'.format(request))

    def download(self, request):
        logger.debug('Requesting {}'.format(request))
        try:
            response = self.session.request(**request.params)
        except Exception as e:
            return self.process_exception(e, request)
        response = Response(response, request)
        logger.debug('Requested {}'.format(response))
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
            logger.warning('Except an iterable object, got {}'.format(type(results)))
        else:
            for x in results:
                self.process_output(x)

    def run(self):
        async def start_request():
            await asyncio.gather(*self._iter_task())
        while self.request_queue.qsize():
            self.event_loop.run_until_complete(start_request())

    def _iter_task(self):
        try:
            for i in range(self.concurrent_requests):
                yield self.crawl(self.next_request())
        except asyncio.queues.QueueEmpty:
                return

    def close(self):
        if isinstance(self.session, requests.Session):
            self.session.close()
        self.event_loop.close()

    def __del__(self):
        self.close()
