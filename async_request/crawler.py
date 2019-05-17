# coding=utf-8

import asyncio
import logging
import requests
import types
from functools import partial
from .request import Request
from .xpath import XpathSelector

logger = logging.getLogger('async_request.Crawler')

class Crawler(object):

    def __init__(self, requests, result_callback=None):
        '''
        init crawler
        :param requests: Request list
        :param result_callback: callback when the result is came out
        :param loop: event loop
        '''
        self.requests = requests
        self.loop = asyncio.get_event_loop()
        self.result_callback = result_callback

    async def get_html(self, request):
        logger.debug('Crawling {}'.format(request.url))
        future = self.loop.run_in_executor(None, partial(requests.request, **request.params))
        while request.retry_times >= 0:
            try:
                response = await future
                break
            except Exception as e:
                logger.info('Error happen when crawling %s' % request.url)
                logger.error(e)
                request.retry_times -= 1
                logger.info('Retrying %s' % request.url)
        else:
            logger.info('Gave up retry %s, total retry %d times' % (request.url, request.retry_times + 1))
            response = requests.Response()
            response.status_code, response.url = 404, request.url

        logger.debug('[%d] Scraped from %s' % (response.status_code, response.url))
        # set meta
        response.meta = request.meta
        # set xpath
        response.xpath = XpathSelector(raw_text=response.text)
        try:
            results = request.callback(response)
        except Exception as e:
            logger.error(e)
            return
        if not isinstance(results, types.GeneratorType):
            return
        # if Request is results, keep request
        for x in results:
            if isinstance(x, Request):
                self.requests.append(x)
            elif self.result_callback:
                self.result_callback(x)

    def run(self, close_eventloop=True):
        try:
            while self.requests:
                tasks = [self.get_html(req) for req in self.requests]
                # clean the request list
                self.requests.clear()
                self.loop.run_until_complete(asyncio.gather(*tasks))
        finally:
            if close_eventloop:
                self.loop.close()
                logger.debug('crawler stopped')