import time
from async_request import Request, crawl, fetch, Crawler


def start():
    req = Request('https://www.baidu.com', callback=parse_baidu)
    c = Crawler([req])
    c.run()


def parse_baidu(response):
    print(response.url, response.status_code)
    for req in [Request(response.url, callback=parse_bing) for i in range(20)]:
        yield req
    yield Request('https://cn.bing.com/', callback=parse_bing)


def parse_bing(response):
    # time.sleep(3)
    print(response.url, response.status_code)
    print(response.xpath('//a/@href').get())
    yield Request('https://www.360.cn/', callback=parse_github)


def parse_github(response):
    print(response.url, response.status_code)
    yield {'hello': 'github'}


def process_result(result):
    print(result)


def parse():
    response = fetch('https://www.bing.com')
    response2 = fetch('https://www.baidu.com')
    print(response, response2)
    print(response.xpath('//a'))
    print(response.xpath('//li'))
    # print(response2.xpath('//a'))


if __name__ == '__main__':
    # request_list = [Request(url='https://www.baidu.com', callback=parse_baidu)]
    # crawl(request_list, result_callback=process_result)

    start()