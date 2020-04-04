from urllib.parse import urljoin

from parsel import Selector
from async_request.request import Request


class Response(object):

    def __init__(self, response, request):
        self._resp = response
        self.text = self._resp.text
        self.request = request

    def __getattr__(self, item):
        return getattr(self._resp, item)

    def __str__(self):
        return f'<Response {self.status_code} {self.url}>'

    __repr__ = __str__

    def recode(self, encoding):
        self.text = self._resp.content.decode(encoding)
        self._init_selector()

    @property
    def meta(self):
        return self.request.meta

    @property
    def selector(self):
        if not hasattr(self, '_selector'):
            self._init_selector()
        return self._selector

    def _init_selector(self):
        self._selector = Selector(text=self.text)

    def xpath(self, query, **kw):
        return self.selector.xpath(query, **kw)

    def css(self, query):
        return self.selector.css(query)

    def urljoin(self, url):
        return urljoin(self.url, url)

    def follow(self, url, *args, **kwargs):
        if isinstance(url, Selector) and url.root.tag == 'a':
            url = url.root.tag.get('href')
            if url is None:
                raise ValueError('selector does not have `href` attribute.')
        elif not isinstance(url, str):
            raise ValueError('param `url` only accept str or Selector type.')

        url = self.urljoin(url)
        return Request(url, *args, **kwargs)
