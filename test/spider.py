import patul


class MySpider(patul.Spider):
    start_urls = ['https://www.baidu.com' for _ in range(1)]

    async def parse(self, response):
        print(response.url)
        yield patul.Request(response.url, callback=self.parse_next)

    def parse_next(self, response):
        print(response.url, ' from parse_next')
        yield {'hello': 'world'}

    def process_result(self, result):
        print(result)


if __name__ == '__main__':
    patul.crawl(MySpider)
