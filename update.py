import asyncio
from typing import List

import aiohttp
import requests
import base64
import urllib3
import logbook.more
import re

gfw_list_url = r"https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt"
logger = logbook.Logger()


async def main():
    async with aiohttp.ClientSession() as session:
        async with session.get(gfw_list_url, proxy='http://localhost:1091') as response:
            txt = await response.text()

    print(txt)


def get_remote_gfwlist():
    urllib3.disable_warnings()
    resp = requests.get(gfw_list_url, proxies={'http': 'socks5://localhost:1090'}, verify=False)
    txt = resp.text

    result = base64.b64decode(txt).decode('utf-8')
    with open(r'gfwlist.txt', 'w') as f:
        f.write(result)


def process_file(filename: str) -> List[str]:
    comment = re.compile(r'^!.*$')
    title = re.compile(r'\[AutoProxy.+]$')
    end_of_file = re.compile(r'!#+General\sList\sEnd#+$')
    kong = re.compile(r'^$')

    pac_list = []
    with open(filename, 'r') as f:
        while line := f.readline():
            if end_of_file.match(line):
                logger.debug('end of file.')
                break
            elif title.match(line) or comment.match(line) or kong.match(line):
                logger.debug('title or comment skipped.')
            else:
                pac_list.append(line[:-1])

    # pac_list.sort()
    return pac_list
    # print(','.join(pac_list))


def fixed(a_list):
    new_list = []
    [new_list.append(i) for i in a_list if i not in new_list]
    return new_list


if __name__ == '__main__':
    logbook.more.ColorizedStderrHandler(level=logbook.INFO).push_application()
    # asyncio.run(main())
    get_remote_gfwlist()
    full_list = process_file(r'gfwlist.txt')
    full_list.extend(process_file(r'extralist.txt'))
    full_list = fixed(full_list)
    full_list.sort()
    # print(len(full_list))

    with open(r'gfwlist.base64.txt', 'w') as f2:
        f2.write(base64.b64encode('\n'.join(full_list).encode('utf-8')).decode('utf-8'))

    # with open(r'gfwlist_ex.txt', 'r') as f3:
    #     t = f3.read()
    #     print(base64.b64decode(t).decode('utf-8'))
