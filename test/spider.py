import asyncio

from aiomysql import create_pool

from async_request import AsyncSpider, Request


class MySpider(AsyncSpider):
    start_urls = ['https://www.baidu.com' for _ in range(2)]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.loop.run_until_complete(self.init_db())

    async def init_db(self):
        self.db = await create_pool(maxsize=3,
                                    host='localhost',
                                    port=3306,
                                    db='lzz',
                                    user='root',
                                    password='1234')

    async def parse(self, response):
        print(response.url)
        for _ in range(2):
            await asyncio.sleep(3)
            yield Request(response.url, callback=self.parse_next)

    def parse_next(self, response):
        print(response.url, ' from parse_next')
        yield {'hello': 'world'}

    async def process_result(self, result):
        async with self.db.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute('SELECT * FROM news LIMIT 1')
                r = await cur.fetchall()
                print(result, r)

    async def closed(self):
        self.db.close()
        await self.db.wait_closed()


if __name__ == '__main__':
    MySpider().run()
