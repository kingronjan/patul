import re
from urllib.parse import urljoin

from parsel import Selector


class Response(object):

    def __init__(self, response, request):
        self._response = response
        self._text = None
        self.request = request

    def __getattr__(self, item):
        return getattr(self._response, item)

    def __str__(self):
        return f'<Response {self.status_code} {self.url}>'

    __repr__ = __str__

    @property
    def meta(self):
        return self.request.meta

    @property
    def text(self):
        if self._text is None:
            charset = re.search(b'charset=(.+?)"', self.content)
            if charset:
                charset = charset.group(1).decode('utf-8')
                try:
                    self._text = self.content.decode(charset)
                except:
                   pass
            if not self._text:
                self._text = self._response.text
        return self._text

    def recoding_text(self, encoding):
        self._text = self.content.decode(encoding)
        return self._text

    @property
    def selector(self):
        if not hasattr(self, '_selector'):
            self._selector = Selector(text=self.text)
        return self._selector

    def xpath(self, query, **kw):
        return self.selector.xpath(query, **kw)

    def css(self, query):
        return self.selector.css(query)

    def urljoin(self, url):
        return urljoin(self.url, url)
