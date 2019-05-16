# async-request
A lightweight network request framework based on requests & asyncio

## install
```shell
pip install async_request
```

## usage
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
DEBUG:asyncio:Using selector: SelectSelector
DEBUG:root:Crawling https://www.baidu.com
DEBUG:requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): www.baidu.com
DEBUG:requests.packages.urllib3.connectionpool:https://www.baidu.com:443 "GET / HTTP/1.1" 200 None
https://www.baidu.com/ 200
DEBUG:root:[200] Scraped from https://www.baidu.com/
DEBUG:root:Crawling https://cn.bing.com/
DEBUG:requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): cn.bing.com
DEBUG:requests.packages.urllib3.connectionpool:https://cn.bing.com:443 "GET / HTTP/1.1" 200 46545
https://cn.bing.com/ 200
DEBUG:root:[200] Scraped from https://cn.bing.com/
DEBUG:root:Crawling https://github.com/financialfly/async-request
DEBUG:requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): github.com
DEBUG:requests.packages.urllib3.connectionpool:https://github.com:443 "GET /financialfly/async-request HTTP/1.1" 200 None
DEBUG:root:[200] Scraped from https://github.com/financialfly/async-request
DEBUG:root:crawler stopped
https://github.com/financialfly/async-request 200
{'hello': 'github'}
```