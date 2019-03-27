#!/usr/bin/env python

from typing import Dict, Any, List
from math import ceil
from itertools import chain

import aiohttp
import asyncio
import re
import time

THREADS = ['qlfg', 'ocfc', 'qwjo', 'qxmo', 'bszzx', 'buacb', 'bvaty']

PATTERN = r'(?:(?:https?|ftp|file):\/\/|www\.|ftp\.)(?:\([-A-Z0-9+&@#\/%=~_|$?!:,.]*\)|[-A-Z0-9+&@#\/%=~_|$?!:,.])*(?:\([-A-Z0-9+&@#\/%=~_|$?!:,.]*\)|[A-Z0-9+&@#\/%=~_|$])'

EXCLUDE_EXT = ['.png', '.jpg', '.jpeg', '.mp4', '.webm', '.avi', '.bmp', '.htm', '.gif', '.dll', '.bms', '.aspx']
EXCLUDE_DOM = ['imgur.com', 'youtube.com', 'steamusercontent.com', 'wikia.com', 'gyazo.com', 'tinypic.com', 'howtogeek.com', 'files.facepunch.com', 'imgbox.com', 'youtu.be']
EXLUCDE_PAT = [r'http://www$']


async def thread_count(session: aiohttp.ClientSession, id: str) -> int:
  """Get the number of pages in a thread."""
  async with session.get(f'https://forum.facepunch.com/dev/{id}/1/?json=1') as response:
    json = await response.json()
    name = json['Thread']['Name']
    count = ceil(json['Page']['Total'] / 30)

    print(f'Found {count} pages in {name} ({id})')

    return count

async def fetch_page(session: aiohttp.ClientSession, id: str, page: int) -> Dict[str, Any]:
  """Fetch a specific page of a thread."""
  try:
    async with session.get(f'https://forum.facepunch.com/dev/{id}/{page}/?json=1') as response:
      return await response.json()
  except aiohttp.client_exceptions.ContentTypeError:
    return dict(Posts=list())

async def fetch_thread(session: aiohttp.ClientSession, id: str) -> List[Dict[str, Any]]:
  """Fetch all the pages of a Facepunch thread by its ID."""
  count = await thread_count(session, id)

  pages = await asyncio.gather(*[fetch_page(session, id, page) for page in range(1, count + 1)])

  return pages

def parse_post(post: Dict[str, Any]) -> int:
  """Find all URLs within a post."""
  matches = re.findall(PATTERN, post['Message'], re.I | re.M)

  return matches

async def main():
  async with aiohttp.ClientSession() as session:
    threads = await asyncio.gather(*[fetch_thread(session, id) for id in THREADS])

    parsed = [parse_post(post) for thread in threads for page in thread for post in page['Posts']]

    count = 0

    with open('links.txt', 'w') as f:
      for thread in parsed:
        if thread is None:
          continue
        for link in thread:
          if any(ext in link.lower() for ext in EXCLUDE_EXT):
            continue
          if any(domain in link.lower() for domain in EXCLUDE_DOM):
            continue

          if any(re.match(pattern, link, re.I) for pattern in EXLUCDE_PAT):
            continue

          f.write(f'{link}\n')
          count += 1
    
    print(f'Wrote {count} links to \'links.txt\'')

if __name__ == '__main__':
  loop = asyncio.get_event_loop()

  try:
    loop.run_until_complete(main())
  except Exception as error:
    loop.close()
    raise error
