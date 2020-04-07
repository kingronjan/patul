from .crawler import Crawler
from .request import Request, FormRequest
from .spider import Spider, crawl


def fetch(url_or_request, **kwargs):
    crawler_kwargs = kwargs.pop('crawler_kwargs', {})
    crawler_kwargs.setdefault('max_retries', 0)
    crawler_kwargs.setdefault('concurrent_requests', 1)

    if isinstance(url_or_request, str):
        req = Request(url_or_request, **kwargs)
    elif isinstance(url_or_request, Request):
        req = url_or_request
    else:
        raise ValueError(f'unexpect type of param `url_or_request`: {type(url_or_request)}')

    resp = None

    if req.callback is None:
        def parse(response):
            nonlocal resp
            resp = response

        req.callback = parse

    with Crawler(**crawler_kwargs) as c:
        c.put_request(req)
        c.run()

    return resp
