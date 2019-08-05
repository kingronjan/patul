# coding=utf-8

import asyncio
import logging
import sys
import traceback
import types
from functools import partial

import requests

from .request import Request
from .response import Response

logger = logging.getLogger('async_request.Crawler')


class Crawler(object):

    def __init__(self, reqs, result_callback=None):
        '''
        init crawler
        :param reqs: Request list
        :param result_callback: callback when the result is came out
        :param loop: event loop
        '''
        self.requests = reqs
        self.loop = asyncio.get_event_loop()
        self.result_callback = result_callback
        self.session = requests.Session()

    async def get_html(self, request):
        logger.debug('Crawling {}'.format(request.url))
        future = self.loop.run_in_executor(None, partial(self.session.request, **request.params))
        while request.retry_times >= 0:
            try:
                response = await future
                break
            except Exception as e:
                self._trace_error()
                request.retry_times -= 1
                logger.info('Retrying %s' % request.url)
        else:
            logger.info('Gave up retry %s, total retry %d times' % (request.url, request.retry_times + 1))
            response = requests.Response()
            response.status_code, response.url = 404, request.url

        logger.debug('[%d] Scraped from %s' % (response.status_code, response.url))
        response = Response(response, request)
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
        traceback.print_exception(exc_type, exc_value, exc_traceback_obj, limit=2)

    def run(self):
        while self.requests:
            tasks = [self.get_html(req) for req in self.requests]
            # clean the request list
            self.requests.clear()
            self.loop.run_until_complete(asyncio.gather(*tasks))

    def close(self):
        self.session.close()
        self.loop.close()

    def __del__(self):
        self.close()