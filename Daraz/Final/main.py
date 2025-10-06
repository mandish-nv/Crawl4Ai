from crawlScrap import crawlScrap
from llm import llm_process

import asyncio

if __name__=="__main__":
  asyncio.run(crawlScrap())
  llm_process()
  
  