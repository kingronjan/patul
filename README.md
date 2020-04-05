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
    
   
if __name__ == '__main__':
    parse()
```
the output will like this:
```
<Response 200 https://cn.bing.com/>
```

Use the `test` decorator is also a method to test spider:
```python
import patul


@patul.test('https://www.baidu.com')
def parse(response):
    print(response.url, response.status_code)
    
    
if __name__ == '__main__':
    parse()
```
then run the script, you will see the result:
```
https://www.baidu.com/ 200
```
