import asyncio
import base64
import re

import aiofile
import aiohttp
from typing import List

import logbook.more

# 清单地址
GFW_LIST_URL = r"https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt"

# logger
logger = logbook.Logger()

# aiodns 临时方案
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# re
comment_re = re.compile(r'^!.*$')
title_re = re.compile(r'\[AutoProxy.+]$')
end_of_file_re = re.compile(r'!#+General\sList\sEnd#+$')
empty_line_re = re.compile(r'^$')


async def get_remote_gfwlist_file_async(save_filename: str):
    resolver = aiohttp.resolver.AsyncResolver(nameservers=["8.8.8.8", "8.8.4.4"])
    conn = aiohttp.TCPConnector(resolver=resolver)

    async with aiohttp.ClientSession(connector=conn) as session:
        async with session.get(GFW_LIST_URL) as response:
            txt = await response.content.read()

    result = base64.decodebytes(txt).decode('utf-8')
    async with aiofile.async_open(save_filename, 'w') as f:
        await f.write(result)


async def get_pac_items_async(*args: str) -> List[str]:
    pac_list: List[str] = []
    final_pac_list: List[str] = []

    for filename in args:
        await __process_file_async(pac_list, filename)

    # 去重
    [final_pac_list.append(i) for i in pac_list if i not in final_pac_list]

    # 排序
    final_pac_list.sort()
    return final_pac_list


async def __process_file_async(items: List[str], name: str):
    async with aiofile.async_open(name, 'r') as f:
        while line := await f.readline():
            if end_of_file_re.match(line):
                logger.debug('end of file.')
                break
            elif title_re.match(line) or comment_re.match(line) or empty_line_re.match(line):
                logger.debug('title_re or comment_re skipped.')
            else:
                items.append(line[:-1])


async def build_gfwlist(filename: str, pac_items: List[str]):
    async with aiofile.async_open(filename, 'w') as f2:
        await f2.write(base64.encodebytes('\n'.join(pac_items).encode('utf-8')).decode('utf-8'))


async def main():
    await get_remote_gfwlist_file_async(r'gfwlist.txt')
    result = await get_pac_items_async(r'gfwlist.txt', r'extralist.txt')
    await build_gfwlist(r'gfwlist.base64.txt', result)

    # test
    # async with aiofile.async_open(r'gfwlist2.base64.txt', 'r') as f3:
    #     txt: str = await f3.read()
    # print(base64.decodebytes(txt.encode('utf-8')).decode('utf-8'))


if __name__ == '__main__':
    logbook.more.ColorizedStderrHandler(level=logbook.INFO).push_application()
    asyncio.run(main())
