from patul.crawler import Crawler
from patul.request import Request


class Fetcher(object):

    _crawler = None

    @classmethod
    def crawler(cls):
        if cls._crawler is None:
            cls._crawler = Crawler(max_retries=0)
        return cls._crawler

    def _make_request(self, url_or_request, **kwargs):
        if isinstance(url_or_request, str):
            if kwargs.get('callback'):
                raise TypeError("can't assign the callback argument to _Fetcher object")
            return Request(url_or_request, **kwargs)
        return url_or_request

    def _run(self):
        if not self.crawler().loop.is_running():
            self.crawler().run(close_loop=False)

    def _put_request(self, request):
        self.crawler().put_request(request)

    def fetch(self, url_or_request, **request_kw):

        r = None

        @self.test(url_or_request, **request_kw)
        def parse(response):
            nonlocal r
            r = response

        parse()
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
            self._put_request(request)
            return self._run

        return test


fetcher = Fetcher()
fetch = fetcher.fetch
test = fetcher.test
