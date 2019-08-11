# coding=utf-8

import asyncio
import logging
import sys
import traceback
import types
from functools import partial

import requests
from requests.exceptions import ConnectionError, ProxyError, ConnectTimeout, ReadTimeout

from .request import Request
from .response import Response

logger = logging.getLogger('async_request.Crawler')


class Crawler(object):

    def __init__(self, reqs,
                 result_callback=None,
                 handle_cookies=True,
                 download_delay=0,
                 concurrent_requests=10,
                 priority=-1):
        '''
        :param reqs: Request list
        :param result_callback: function to process the result
        :param handle_cookies: handle the cookies or not
        :param download_delay: delayed time before download
        :param concurrent_requests: max concurrent requests
        :param priority: -1: first in last out
                          0: first in first out
        '''
        self.requests = reqs
        self.loop = asyncio.get_event_loop()
        self.result_callback = result_callback
        self.session = requests.Session() if handle_cookies else requests
        self.download_delay = download_delay
        self.concurrent_requests = concurrent_requests
        self.priority = priority

    def iter_requests(self):
        for i in range(self.concurrent_requests):
            try:
                yield self.requests.pop(self.priority)
            except IndexError:
                break

    async def get_html(self, request):
        logger.debug('Crawling {}'.format(request))
        future = self.loop.run_in_executor(None, partial(self.session.request, **request.params))
        while request.retry_times >= 0:
            try:
                await asyncio.sleep(self.download_delay)
                response = await future
                break
            except (ConnectTimeout, ConnectionError, ProxyError, ReadTimeout) as e:
                logger.error(e)
            except Exception as e:
                self._trace_error()
            request.retry_times -= 1
            logger.info('Retrying %s' % request.url)
        else:
            logger.info('Gave up retry %s, total retry %d times' % (request.url, request.retry_times + 1))
            return

        response = Response(response, request)
        logger.debug('[%d] Crawled from {}'.format(response))
        try:
            results = request.callback(response)
        except Exception as e:
            self._trace_error()
            return
        if not isinstance(results, types.GeneratorType):
            return
        # if results include Request, keep request
        for x in results:
            if isinstance(x, Request):
                self.requests.append(x)
            elif self.result_callback:
                self.result_callback(x)

    def _trace_error(self):
        exc_type, exc_value, exc_traceback_obj = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback_obj, limit=3)

    def run(self):
        while self.requests:
            tasks = [self.get_html(req) for req in self.iter_requests()]
            self._run_tasks(*tasks)

    def _run_tasks(self, *tasks):
        self.loop.run_until_complete(asyncio.gather(*tasks))

    def close(self):
        if isinstance(self.session, requests.Session):
            self.session.close()
        self.loop.close()

    def __del__(self):
        self.close()