from async_request.crawler import Crawler
from async_request.request import Request
from async_request.utils import coro_wrapper


class AsyncSpider(object):

    start_urls = None

    def __init__(self, loop):
        self.loop = loop

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


def crawl_spider(spider_cls, close_loop=True, **kwargs):
    crawler = Crawler(**kwargs)
    loop = crawler.loop
    spider = spider_cls(loop)
    crawler.result_back = spider.process_result

    for request in spider.start_requests():
        if not request.callback:
            request.callback = spider.parse
        crawler.put_request(request)

    try:
        loop.run_until_complete(spider.__async_init__())
        crawler.run(close_loop=False)
    finally:
        try:
            coro = coro_wrapper(spider.closed())
            loop.run_until_complete(coro)
        finally:
            if close_loop:
                loop.close()
