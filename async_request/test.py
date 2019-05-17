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

request_list = [ar.Request(url='https://www.baidu.com', callback=parse_baidu)]
ar.crawl(request_list, result_callback=process_result)