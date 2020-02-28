from async_request.crawler import Crawler
from async_request.request import Request


class AsyncSpider(object):

    start_urls = None

    def __init__(self, **kwargs):
        kwargs.setdefault('result_back', self.process_result)
        self.crawler = Crawler(**kwargs)

    def start_request(self):
        for url in self.start_urls or []:
            self.crawler.add_request(Request(url, callback=self.parse))

    def parse(self, response):
        pass

    def process_result(self, result):
        pass

    def closed(self):
        pass

    def run(self, close_after_crawled=True):
        try:
            self.start_request()
            self.crawler.run(close_after_crawled)
        finally:
            self.closed()
