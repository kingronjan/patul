import re
from async_request.xpath import Xpath
from urllib.parse import urljoin

_default_coding = 'utf-8'

class Response(object):

    def __init__(self, response, request):
        self._response = response
        self.content = response.content
        self.status = response.status_code
        self.url = response.url
        self.request = request

    def __getattr__(self, item):
        return getattr(self._response, item)

    @property
    def meta(self):
        return self.request.meta

    @property
    def text(self):
        if hasattr(self, '_text'):
            return self._text
        charset = re.search(b'charset=(.+?)"', self.content)
        if charset:
            charset = charset.group(1).decode('utf-8')
            try:
                text = self.content.decode(charset)
            except:
                text = self.content.decode(_default_coding)
        else:
            text = self.content.decode(_default_coding)
        self._text = text
        return self._text

    def xpath(self, syntax):
        if not hasattr(self, '_xpath_selector'):
            self._xpath_selector = Xpath(self.text)
        return self._xpath_selector(syntax)

    def urljoin(self, url):
        return urljoin(self.url, url)