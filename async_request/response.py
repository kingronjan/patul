import re
from async_request.xpath import Xpath
from urllib.parse import urljoin

class Response(object):

    def __init__(self, response, request):
        self.content = response.content
        self.status = response.status_code
        self.url = response.url
        self.request = request
        self._set_text()
        self._set_xpath()
        del response

    @property
    def meta(self):
        return self.request.meta

    def _set_text(self):
        charset = re.search(b'charset=(.*?)"', self.content)
        if charset:
            charset = charset.group(1).decode('utf-8')
            self.text = self.content.decode(charset)
        else:
            self.text = self.content.decode('utf-8')

    def _set_xpath(self):
        self.xpath = Xpath(self.text)

    def urljoin(self, url):
        return urljoin(self.url, url)