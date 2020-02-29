from collections import Coroutine

from async_request.crawler import Crawler
from async_request.request import Request


class AsyncSpider(object):

    start_urls = None

    def __init__(self, **kwargs):
        kwargs.setdefault('result_back', self.process_result)
        self.crawler = Crawler(**kwargs)
        self.loop = self.crawler.loop

    def start_requests(self):
        for url in self.start_urls or []:
            yield Request(url)

    def parse(self, response):
        pass

    def process_result(self, result):
        pass

    def closed(self):
        pass

    def close(self, close_loop):
        try:
            _ = self.closed()
            if isinstance(_, Coroutine):
                self.loop.run_until_complete(_)
        finally:
            if close_loop:
                self.loop.close()

    def run(self, close_loop=True):
        try:
            for request in self.start_requests():
                if not request.callback:
                    request.callback = self.parse
                self.crawler.put_request(request)
            self.crawler.run(close_loop=False)
        finally:
            self.close(close_loop)
