import functools

from async_request.crawler import Crawler
from async_request.request import Request


class AsyncFetcher(object):

    def __init__(self):
        self._crawler = None

    def __del__(self):
        if self._crawler is not None:
            self._crawler.close()

    @property
    def crawler(self):
        if self._crawler is None:
            self._crawler = Crawler()
        return self._crawler

    def _make_request(self, url_or_request, **kwargs):
        if isinstance(url_or_request, str):
            if kwargs.get('callback'):
                raise TypeError("can't assign the callback argument to _Fetcher object")
            return Request(url_or_request, **kwargs)
        return url_or_request

    def fetch(self, url_or_request, **request_kw):
        request = self._make_request(url_or_request, **request_kw)
        r = None

        def parse(response):
            nonlocal r
            r = response

        request.callback = parse
        self.crawler.put_request(request)
        self.crawler.run(close_loop=False)
        return r

    def test(self, url_or_request, **request_kw):
        """A decorator to test request
        Usage:

            @fetcher.test('http://xxx.xx.com')
            def parse(response):
                # do something

        and run the function like this:

            parse()
        """
        request = self._make_request(url_or_request, **request_kw)

        def test(func):
            request.callback = func
            self.crawler.put_request(request)
            return functools.partial(self.crawler.run, close_loop=False)

        return test
