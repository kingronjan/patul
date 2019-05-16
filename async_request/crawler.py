# coding=utf-8

import asyncio
import logging
import requests
import types
from functools import partial
from .request import Request

logger = logging.getLogger('async_request.Crawler')

class Crawler(object):

    def __init__(self, requests, result_callback=None):
        '''
        初始化crawler
        :param requests: Request请求列表
        :param result_callback: 请求结束后的结果处理回调函数
        :param logger: logger
        '''
        self.requests = requests
        self.loop = asyncio.get_event_loop()
        self.result_callback = result_callback

    async def get_html(self, request):
        logging.debug('Crawling {}'.format(request.url))
        future = self.loop.run_in_executor(None,
                                           partial(requests.request,
                                                   method=request.method,
                                                   url=request.url,
                                                   headers=request.headers,
                                                   timeout=request.timeout,
                                                   cookies=request.cookies,
                                                   proxies=request.proxies,
                                                   data=request.data,
                                                   json=request.json
                                                   ))
        while request.retry_times >= 0:
            try:
                r = await future
                break
            except Exception as e:
                logger.info('Error happen when crawling %s' % request.url)
                logger.error(e)
                request.retry_times -= 1
                logger.info('Retrying %s' % request.url)
        else:
            logger.info('Gave up retry %s, total retry %d times' % (request.url, request.retry_times + 1))
            r = requests.Response()
            r.status_code, r.url = 404, request.url

        logger.debug('[%d] Scraped from %s' % (r.status_code, r.url))
        # 传递meta
        r.meta = request.meta
        results = request.callback(r)
        if not isinstance(results, types.GeneratorType):
            return
        # 检测结果，如果是Request，则添加到requests列表中准备继续请求，否则执行结果回调函数
        for x in results:
            if isinstance(x, Request):
                self.requests.append(x)
            elif self.result_callback:
                self.result_callback(x)

    def run(self):
        # 如果requests列表中还有Request实例，则继续请求
        while self.requests:
            tasks = [self.get_html(req) for req in self.requests]
            # 重置为空列表
            self.requests = list()
            self.loop.run_until_complete(asyncio.gather(*tasks))

    def stop(self):
        self.loop.close()
        logging.debug('crawler stopped')