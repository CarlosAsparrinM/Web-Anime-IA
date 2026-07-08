import asyncio
from agents.sources import fetch_random_anime, fetch_seasonal_anime, fetch_top_anime

async def run_tests():
    print("=== Testing AniList Fallback ===")
    
    # We will temporarily mock the Jikan URL to fail by monkeypatching httpx in the script,
    # or we can just call fetch_anilist_fallback directly to see what it returns, 
    # but let's test the actual fallback mechanism by replacing the jikan url with a bad one.
    import agents.sources
    import httpx
    
    # Save original get
    original_get = httpx.AsyncClient.get
    
    # Mock to force failure for jikan
    async def mock_get(self, url, **kwargs):
        if "jikan.moe" in url:
            raise Exception("Mocked Jikan Failure")
        return await original_get(self, url, **kwargs)
        
    httpx.AsyncClient.get = mock_get
    
    print("\n1. Testing Random Anime Fallback...")
    try:
        res = await fetch_random_anime()
        print(f"TITLE: {res.get('title')}")
        print(f"SYNOPSIS: {res.get('synopsis')[:100]}...")
        print(f"GENRES: {res.get('genres')}")
        print(f"IMAGE: {res.get('imageUrl')}")
        print(f"STUDIOS: {res.get('studios')}")
        print(f"SCORE: {res.get('score')}")
    except Exception as e:
        print("Failed:", e)
        
    print("\n2. Testing Seasonal Anime Fallback...")
    try:
        res = await fetch_seasonal_anime()
        print(f"TITLE: {res.get('title')}")
    except Exception as e:
        print("Failed:", e)

    print("\n3. Testing Top Anime Fallback...")
    try:
        res = await fetch_top_anime()
        print(f"TITLE: {res.get('title')}")
    except Exception as e:
        print("Failed:", e)

if __name__ == '__main__':
    asyncio.run(run_tests())
