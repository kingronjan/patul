async-request
=============

A lightweight network request framework based on requests & asyncio

install
-------

```bash
pip install async_request
```

usage
-----
```python
import async_request

def parse_baidu(response):
    print(response.url, response.status_code)
    yield async_request.Request('https://cn.bing.com/', callback=parse_bing)

def parse_bing(response):
    print(response.url, response.status_code)
    yield async_request.Request('https://github.com/financialfly/async-request', callback=parse_github)

def parse_github(response):
    print(response.url, response.status_code)
    yield {'hello': 'github'}

def process_result(result):
    print(result)

reqs = [async_request.Request(url='https://www.baidu.com', callback=parse_baidu)]
c = async_request.Crawler(reqs, result_callback=process_result)
c.run()
c.stop()
```
And you'll see the result like this:
```
https://www.baidu.com/ 200
https://cn.bing.com/ 200
https://github.com/financialfly/async-request 200
{'hello': 'github'}
```