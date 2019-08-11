# coding=utf-8

import asyncio
import logging
import sys
import traceback

import requests

from async_request.request import Request
from async_request.response import Response

logger = logging.getLogger('async_request.Crawler')


class Crawler(object):

    def __init__(self, reqs,
                 result_back=None,
                 error_back=None,
                 handle_cookies=True,
                 download_delay=0,
                 concurrent_requests=2,
                 priority=-1,
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
            self.queue = asyncio.Queue()
        elif priority == 1:
            self.queue = asyncio.LifoQueue()
        else:
            raise ValueError('Argument priority expect 1 or -1, got {}'.format(priority))
        for req in reqs:
            self.queue.put_nowait(req)
        self.result_back = result_back
        self.error_back = error_back
        self.session = requests.Session() if handle_cookies else requests
        self.download_delay = download_delay
        self.concurrent_requests = concurrent_requests
        self.event_loop = event_loop or asyncio.get_event_loop()

    def process_exception(self, e, request):
        if self.error_back:
            return self.process_output(self.error_back(e, request))
        exc_type, exc_value, exc_traceback_obj = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback_obj, limit=3)

    def process_output(self, result):
        if isinstance(result, Request):
            self.queue.put_nowait(result)
        elif self.result_back:
            self.result_back(result)

    def download(self, request):
        logger.debug('Crawling {}'.format(request))
        while request.retry_times >= 0:
            try:
                response = self.session.request(**request.params)
                break
            except Exception as e:
                self.process_exception(e, request)
            request.retry_times -= 1
            logger.info('Retrying %s' % request.url)
        else:
            logger.info('Gave up retry %s, total retry %d times' % (request.url, request.retry_times + 1))
            return
        response = Response(response, request)
        logger.debug('[%d] Crawled from {}'.format(response))
        return response

    async def crawl(self, request):
        loop = asyncio.get_running_loop()
        await asyncio.sleep(self.download_delay)
        response = await loop.run_in_executor(None, self.download, request)
        if not response:
            return
        try:
            results = request.callback(response)
            results = iter(results)
        except TypeError:
            logger.warning('Except an iterable object')
            return
        except Exception as e:
            self.process_exception(e, request)
        else:
            for x in results:
                self.process_output(x)

    def run(self):
        async def start_request():
            await asyncio.gather(*self._iter_task())
        while self.queue.qsize():
            self.event_loop.run_until_complete(start_request())

    def _iter_task(self):
        for i in range(self.concurrent_requests):
            try:
                request = self.queue.get_nowait()
                yield self.crawl(request)
            except asyncio.queues.QueueEmpty:
                break

    def close(self):
        if isinstance(self.session, requests.Session):
            self.session.close()
        self.event_loop.close()

    def __del__(self):
        self.close()
