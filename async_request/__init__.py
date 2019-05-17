from .crawler import Crawler
from .request import Request, FormRquest

def crawl(requests, result_callback=None, close_eventloop=True):
    c = Crawler(requests=requests, result_callback=result_callback)
    c.run(close_eventloop=close_eventloop)