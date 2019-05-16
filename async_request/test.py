from async_request import Request, Crawler
#
def parse_baidu(response):
    print(response.url, response.status_code)
    yield Request('https://cn.bing.com/', callback=parse_bing)

def parse_bing(response):
    print(response.url, response.status_code)
    yield Request('https://github.com/financialfly/async-request', callback=parse_github)

def parse_github(response):
    print(response.url, response.status_code)
    yield {'hello': 'github'}

def process_result(result):
    print(result)

c = Crawler([Request(url='https://www.baidu.com', callback=parse_baidu)], result_callback=process_result)
c.run()
c.stop()