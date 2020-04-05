from patul.crawler import Crawler, coro_wrapper
from patul.request import Request


class Spider(object):

    start_urls = None

    def __init__(self, loop):
        self.loop = loop

    async def __ainit__(self):
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


def crawl(spider_cls, close_loop=True, **kwargs):
    crawler = Crawler(**kwargs)
    loop = crawler.loop
    spider = spider_cls(loop)
    crawler.result_back = spider.process_result

    for request in spider.start_requests():
        if not request.callback:
            request.callback = spider.parse
        crawler.put_request(request)

    try:
        loop.run_until_complete(spider.__ainit__())
        crawler.run(close_loop=False)
    finally:
        try:
            coro = coro_wrapper(spider.closed())
            loop.run_until_complete(coro)
        finally:
            if close_loop:
                loop.close()
