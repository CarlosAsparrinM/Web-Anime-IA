import asyncio
import os
import json
from dotenv import load_dotenv
from agents.sources import fetch_random_anime, fetch_anime_news
from agents.tavily import fetch_tavily_research
from ddgs import DDGS

load_dotenv()

async def run_tests():
    print("=== 1. JIKAN API (fetch_random_anime) ===")
    try:
        jikan_data = await fetch_random_anime()
        print("KEYS:", jikan_data.keys())
        print("TITLE:", jikan_data.get('title'))
        print("SYNOPSIS SNIPPET:", jikan_data.get('synopsis', '')[:150])
    except Exception as e:
        print("Jikan API error:", e)

    print("\n=== 2. ANN RSS FEED (fetch_anime_news) ===")
    try:
        news_data = await fetch_anime_news()
        print("KEYS:", news_data.keys())
        print("TITLE:", news_data.get('title'))
        print("SYNOPSIS SNIPPET:", news_data.get('synopsis', '')[:150])
        print("IMAGE_URL:", news_data.get('imageUrl'))
    except Exception as e:
        print("ANN RSS error:", e)

    print("\n=== 3. DUCKDUCKGO IMAGES ===")
    try:
        # DDGS search is synchronous in ddgs 9.14.4
        results = DDGS().images("Naruto official art wallpaper", max_results=2)
        if results:
            print("FOUND:", len(results))
            print("FIRST IMAGE DICT KEYS:", results[0].keys() if isinstance(results[0], dict) else type(results[0]))
            print("FIRST IMAGE URL:", results[0].get('image') if isinstance(results[0], dict) else results[0])
    except Exception as e:
        print("DDGS error:", e)

    print("\n=== 4. TAVILY API (10 Searches) ===")
    queries = [
        "Naruto hidden secrets trivia",
        "One Piece Oda interviews trivia",
        "Bleach thousand year blood war animation production",
        "Attack on Titan ending controversy",
        "Jujutsu Kaisen manga sales records",
        "Demon Slayer Mugen Train box office analysis",
        "Evangelion Hideaki Anno depression influence",
        "Cowboy Bebop jazz music Yoko Kanno",
        "Fullmetal Alchemist Brotherhood differences from original",
        "Death Note rules of the death note"
    ]
    for i, q in enumerate(queries):
        try:
            print(f"  [{i+1}/10] Query: '{q}'")
            res, img = await fetch_tavily_research(q, "curiosidades")
            print(f"      RESULTS: {len(res)}")
            if res:
                print(f"      FIRST TITLE: {res[0].get('title')}")
                print(f"      SNIPPET: {res[0].get('content', '')[:100].replace(chr(10), ' ')}")
        except Exception as e:
            print(f"      Error: {e}")

if __name__ == '__main__':
    asyncio.run(run_tests())
