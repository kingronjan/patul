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
from async_request import Request, crawl


def parse_baidu(response):
    print(response.url, response.status_code)
    yield Request('https://cn.bing.com/', callback=parse_bing)


def parse_bing(response):
    print(response.url, response.status_code)
    print(response.xpath('//a/@href').get())
    yield Request('https://github.com/financialfly/async-request', callback=parse_github)


def parse_github(response):
    print(response.url, response.status_code)
    yield {'hello': 'github'}


def process_result(result):
    print(result)


if __name__ == '__main__':
    request_list = [Request(url='https://www.google.com', callback=parse_baidu)]
    crawl(request_list, result_callback=process_result)
```
And you'll see the result like this:
```
https://www.baidu.com/ 200
https://cn.bing.com/ 200
javascript:void(0)
https://github.com/financialfly/async-request 200
{'hello': 'github'}
```

test
----
Use `fetch` function to get a response immediately:
```python
from async_request import fetch

def parse():
    response = fetch('https://www.bing.com')
    print(response)
    
   
if __name__ == '__main__':
    parse()
```
the output will like this:
```
<async_request.Response 200 https://cn.bing.com/>
```

Use the `test` decorator is also a method to test spider:
```python
import async_request as ar


@ar.test('https://www.baidu.com')
def parse(response):
    print(response.url, response.status_code)
    
    
if __name__ == '__main__':
    parse()
```
then run the script, you will see the result:
```
https://www.baidu.com/ 200
```
