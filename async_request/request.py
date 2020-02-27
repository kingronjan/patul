# coding=utf-8

'''
Request
'''
import random

from requests.cookies import RequestsCookieJar

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:65.0) Gecko/20100101 Firefox/65.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/18.17763',
    'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 10.0; WOW64; Trident/7.0; .NET4.0C; .NET4.0E; .NET CLR 2.0.50727; .NET CLR 3.0.30729; .NET CLR 3.5.30729)',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.101',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.122',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.71',
    'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)',
    'Mozilla/5.0 (Windows NT 5.1; U; en; rv:1.8.1) Gecko/20061208 Firefox/2.0.0 Opera 9.50',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0',
]


class Request(object):

    def __init__(self, url, params=None, headers=None,
                 timeout=5, callback=None, meta=None,
                 cookies=None, proxies=None, method='GET', **kwargs):
        '''
        Request object
        :param url: request url
        '''
        self.url = url
        self.params = params
        self._headers = headers
        self._cookies = cookies
        self.timeout = timeout
        self.proxies = proxies
        self.method = method
        self.callback = callback
        self.meta = meta or {}
        kwargs.setdefault('allow_redirects', True)
        # it will as a kwargs send to requests.request
        self.request_kwargs = self._form_kwargs(**kwargs)

    def _form_kwargs(self, **kwargs):
        return {
            'url': self.url,
            'params': self.params,
            'headers': self.headers,
            'cookies': self.cookies,
            'timeout': self.timeout,
            'proxies': self.proxies,
            'method': self.method,
            **kwargs
        }

    @property
    def headers(self):
        if self._headers is None:
            return {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en',
                'User-Agent': random.choice(USER_AGENTS)
            }
        return self._headers

    @property
    def cookies(self):
        if isinstance(self._cookies, list):
            jar = RequestsCookieJar()
            for c in self._cookies:
                jar.set(c['name'], c['value'], domains=c['domains'], path=c['path'])
            return jar
        return self._cookies

    def __str__(self):
        return f'<Request {self.method} {self.url}>'


class FormRequest(Request):

    def __init__(self, url, data=None, json=None, method='POST', **kwargs):
        self.data = data
        self.json = json
        super().__init__(url=url, method=method, **kwargs)

    def _form_kwargs(self, **kwargs):
        kw = super()._form_kwargs(**kwargs)
        kw['data'] = self.data
        kw['json'] = self.json
        return kw
