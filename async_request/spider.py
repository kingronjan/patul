from async_request.crawler import Crawler
from async_request.request import Request
from async_request.utils import async_func


class AsyncSpider(object):

    start_urls = None

    def __init__(self, **kwargs):
        kwargs.setdefault('result_back', self.process_result)
        self.crawler = Crawler(**kwargs)
        self.loop = self.crawler.loop
        self.loop.run_until_complete(self.__async_init__())

    async def __async_init__(self):
        pass

    def start_requests(self):
        for url in self.start_urls or []:
            yield Request(url)

    def parse(self, response):
        pass

    def process_result(self, result):
        pass

    def closed(self):
        pass

    async def close(self):
        await async_func(self.closed())

    def run(self, close_loop=True):
        try:
            for request in self.start_requests():
                if not request.callback:
                    request.callback = self.parse
                self.crawler.put_request(request)
            self.crawler.run(close_loop=False)
        finally:
            try:
                self.loop.run_until_complete(self.close())
            finally:
                if close_loop:
                    self.loop.close()
