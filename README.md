patul
=====

A tiny spider based on asyncio and requests.

install
-------

```bash
pip install patul
```

usage
-----
Just like scrapy:
```python
import patul


class MySpider(patul.Spider):
    
    start_urls = ['https://cn.bing.com/']
    
    async def parse(self, response):
        print(response.xpath('//a/@href').get())
        yield patul.Request('https://github.com/financialfly/async-request', callback=self.parse_github)

    def parse_github(self, response):
        yield {'hello': 'github'}
    
    async def process_result(self, result):
        # Process result at here.
        print(result)


if __name__ == '__main__':
    # Run spider
    patul.crawl(MySpider)
```
For more detailed control (like: handle cookies, download delay, concurrent requests, max retries, logs settings etc.): (refer to the constructor of the `Crawler` class):
```python
import patul

class MySpider(patul.Spider):
    ...

if __name__ == '__main__':
    patul.crawl(
        MySpider, 
        handle_cookies=True, 
        download_delay=0, 
        concurrent_requests=10, 
        max_retries=3, 
        log_settings={'fp': 'spider.log'}
    )
```

test
----
Use `fetch` function to get a response immediately:
```python
from patul import fetch


def parse():
    response = fetch('https://www.bing.com')
    print(response)
    
   
parse()
```
the output will like this:
```
<Response 200 https://cn.bing.com/>
```

The `fetch` function also could be use like this:
```python
import patul


def parse(response):
    print(response)
    yield patul.Request(response.url, callback=parse_next)


def parse_next(response):
    print(response.status_code)
    yield {'hello': 'world'}


patul.fetch('http://www.baidu.com', callback=parse)
```
then run the script, you will see the result:
```
<Response 200 http://www.baidu.com/>
200
```
