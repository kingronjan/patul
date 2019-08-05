from .crawler import Crawler
from .request import Request, FormRquest


def crawl(requests, result_callback=None, stop_after_crawled=True):
    c = Crawler(reqs=requests, result_callback=result_callback)
    c.run()
    if stop_after_crawled:
        c.close()


__crawler = None
def test(url_or_request, **request_kw):
    """A decorator to test request
    Usage:

        @test('http://xxx.xx.com')
        def parse(response):
            # do something

    and run the function like this:

        parse()
    """
    if isinstance(url_or_request, str):
        if request_kw.get('callback'):
            raise TypeError("Can't assign the callback argument to a test decorator")
        url_or_request = Request(url_or_request, **request_kw)

    global __crawler
    if __crawler is None:
        __crawler = Crawler([])

    def test(func):
        url_or_request.callback = func
        __crawler.requests.append(url_or_request)
        return __crawler.run
    return test


def fetch(url_or_request, **kwargs):
    """This method will return a response immediately"""
    r = None

    @test(url_or_request, **kwargs)
    def parse(response):
        nonlocal r
        r = response

    parse()
    return r
