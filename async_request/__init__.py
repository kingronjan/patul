from .crawler import Crawler, partial
from .request import Request, FormRquest


def crawl(requests, result_callback=None, close_eventloop=True):
    c = Crawler(requests=requests, result_callback=result_callback)
    c.run(close_eventloop=close_eventloop)


def test(url, req_cls=Request, **req_kw):
    def test(func):
        req = req_cls(url, callback=func, **req_kw)
        if req_kw.get('callback'):
            raise TypeError('Cant assign the callback argument to a test decorator.')
        return partial(crawl, [req])

    return test
