import asyncio
import os
from dotenv import load_dotenv
from agents.tavily import fetch_tavily_research

load_dotenv()

async def run():
    res, img = await fetch_tavily_research('Neon Genesis Evangelion anime trivia', 'curiosidades')
    print('RESULTS LENGTH:', len(res))
    if res:
        print('FIRST RESULT KEYS:', res[0].keys())
        print('FIRST RESULT CONTENT SNIPPET:', res[0].get('content', '')[:200])
        print('FIRST RESULT RAW CONTENT SNIPPET:', res[0].get('raw_content', '')[:200])
        
if __name__ == '__main__':
    asyncio.run(run())
