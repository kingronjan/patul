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
import async_request as ar


def parse_baidu(response):
    print(response.url, response.status_code)
    yield ar.Request('https://cn.bing.com/', callback=parse_bing)


def parse_bing(response):
    print(response.url, response.status_code)
    print(response.xpath('//a/@href').get())
    yield ar.Request('https://github.com/financialfly/async-request', callback=parse_github)


def parse_github(response):
    print(response.url, response.status_code)
    yield {'hello': 'github'}


def process_result(result):
    print(result)


if __name__ == '__main__':
    request_list = [ar.Request(url='https://www.baidu.com', callback=parse_baidu)]
    ar.crawl(request_list, result_callback=process_result)
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
You can test your spider like this:
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