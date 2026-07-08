import httpx
import random
import feedparser
import asyncio
import re

async def fetch_anilist_fallback(sort_method="POPULARITY_DESC", max_page=100) -> dict:
    print(f"--> Using AniList Fallback (sort: {sort_method})...")
    query = '''
    query ($page: Int, $sort: [MediaSort]) {
      Page(page: $page, perPage: 1) {
        media(type: ANIME, sort: $sort) {
          id
          title {
            english
            romaji
          }
          description(asHtml: false)
          coverImage {
            extraLarge
          }
          genres
          averageScore
          seasonYear
          studios(isMain: true) {
            nodes {
              name
            }
          }
          episodes
          status
        }
      }
    }
    '''
    page = random.randint(1, max_page)
    variables = {"page": page, "sort": [sort_method]}
    
    async with httpx.AsyncClient() as client:
        res = await client.post("https://graphql.anilist.co", json={"query": query, "variables": variables}, timeout=10.0)
        data = res.json()
        
        if "errors" in data or not data.get("data", {}).get("Page", {}).get("media"):
            raise Exception(f"AniList API error: {data}")
            
        anime = data["data"]["Page"]["media"][0]
        title = anime.get("title", {}).get("english") or anime.get("title", {}).get("romaji") or "Unknown Title"
        desc = anime.get("description") or "No synopsis available."
        clean_desc = re.sub(r'<[^>]+>', '', desc)
        studios = [node["name"] for node in anime.get("studios", {}).get("nodes", [])] if anime.get("studios") else ["Unknown"]
        status_map = {
            "FINISHED": "Finished Airing", "RELEASING": "Currently Airing",
            "NOT_YET_RELEASED": "Not yet aired", "CANCELLED": "Cancelled", "HIATUS": "Hiatus"
        }
        
        return {
            "mal_id": anime.get("id"),
            "title": title,
            "synopsis": clean_desc,
            "imageUrl": anime.get("coverImage", {}).get("extraLarge", ""),
            "genres": anime.get("genres", []),
            "score": (anime.get("averageScore") / 10) if anime.get("averageScore") else None,
            "year": anime.get("seasonYear"),
            "studios": studios,
            "episodes": anime.get("episodes", "Unknown"),
            "status": status_map.get(anime.get("status"), "Unknown"),
            "extraImages": []
        }

async def get_extra_images(mal_id: int) -> list:
    try:
        await asyncio.sleep(0.4) # Jikan rate limits
        async with httpx.AsyncClient() as client:
            res = await client.get(f"https://api.jikan.moe/v4/anime/{mal_id}/pictures", timeout=10.0)
            data = res.json()
            if not data.get("data"):
                return []
            return [p["jpg"]["large_image_url"] for p in data["data"]][:5]
    except Exception:
        return []

def format_jikan_data(anime: dict) -> dict:
    return {
        "mal_id": anime.get("mal_id"),
        "title": anime.get("title_english") or anime.get("title"),
        "synopsis": anime.get("synopsis") or "No synopsis available.",
        "imageUrl": anime.get("images", {}).get("jpg", {}).get("large_image_url", ""),
        "genres": [g["name"] for g in anime.get("genres", [])],
        "score": anime.get("score"),
        "year": anime.get("year"),
        "studios": [s["name"] for s in anime.get("studios", [])] if anime.get("studios") else ["Unknown"],
        "episodes": anime.get("episodes", "Unknown"),
        "status": anime.get("status", "Unknown")
    }

async def fetch_random_anime() -> dict:
    try:
        page = random.randint(1, 50)
        async with httpx.AsyncClient() as client:
            res = await client.get(f"https://api.jikan.moe/v4/anime?order_by=score&sort=desc&page={page}", timeout=10.0)
            data = res.json()
            if "data" not in data or not data["data"]:
                raise Exception(f"Jikan API error in random_anime: {data.get('message', data)}")
            index = random.randint(0, len(data["data"]) - 1)
            anime = data["data"][index]
            formatted = format_jikan_data(anime)
            formatted["extraImages"] = await get_extra_images(anime["mal_id"])
            return formatted
    except Exception as e:
        print(f"Jikan random_anime failed: {e}. Falling back to AniList...")
        return await fetch_anilist_fallback(sort_method="POPULARITY_DESC", max_page=150)

async def fetch_seasonal_anime() -> dict:
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get("https://api.jikan.moe/v4/seasons/now", timeout=10.0)
            data = res.json()
            if "data" not in data or not data["data"]:
                raise Exception(f"Jikan API error in seasonal_anime: {data.get('message', data)}")
            index = random.randint(0, len(data["data"]) - 1)
            anime = data["data"][index]
            formatted = format_jikan_data(anime)
            formatted["extraImages"] = await get_extra_images(anime["mal_id"])
            return formatted
    except Exception as e:
        print(f"Jikan seasonal_anime failed: {e}. Falling back to AniList...")
        return await fetch_anilist_fallback(sort_method="TRENDING_DESC", max_page=3)

async def fetch_top_anime() -> dict:
    try:
        page = random.randint(1, 5)
        async with httpx.AsyncClient() as client:
            res = await client.get(f"https://api.jikan.moe/v4/top/anime?page={page}", timeout=10.0)
            data = res.json()
            if "data" not in data or not data["data"]:
                raise Exception(f"Jikan API error in top_anime: {data.get('message', data)}")
            index = random.randint(0, len(data["data"]) - 1)
            anime = data["data"][index]
            formatted = format_jikan_data(anime)
            formatted["extraImages"] = await get_extra_images(anime["mal_id"])
            return formatted
    except Exception as e:
        print(f"Jikan top_anime failed: {e}. Falling back to AniList...")
        return await fetch_anilist_fallback(sort_method="SCORE_DESC", max_page=5)

async def fetch_anime_news() -> dict:
    feed = feedparser.parse('https://www.animenewsnetwork.com/newsroom/rss.xml')
    items = [item for item in feed.entries if hasattr(item, 'title') and hasattr(item, 'summary')]
    
    if not items:
        raise Exception("No news found")
    
    item = random.choice(items[:min(3, len(items))])
    
    # Intentar extraer una imagen del feed o de la URL original
    extracted_image = None
    
    # Estrategia 1: Atributos estándar de RSS (por si el feed cambia a futuro)
    if hasattr(item, 'media_thumbnail') and item.media_thumbnail:
        extracted_image = item.media_thumbnail[0]['url']
    elif hasattr(item, 'content'):
        img_match = re.search(r'<img[^>]+src="([^">]+)"', item.content[0].value)
        if img_match:
            extracted_image = img_match.group(1)
            
    # Estrategia 2: Scrapear el og:image directamente de la noticia de ANN (ya que su RSS no tiene imágenes)
    if not extracted_image and hasattr(item, 'link'):
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(item.link, timeout=10.0)
                # Buscar la etiqueta meta property="og:image" content="..."
                og_match = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', res.text)
                if not og_match:
                    og_match = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', res.text)
                
                if og_match:
                    extracted_image = og_match.group(1)
        except Exception:
            pass
            
    # Fallback image
    final_image = extracted_image if extracted_image else "https://images.unsplash.com/photo-1578632767115-351597cf2477?q=80&w=800&auto=format&fit=crop"
    
    # Remove HTML tags from summary for a clean synopsis
    clean_summary = re.sub(r'<[^>]+>', '', item.summary) if hasattr(item, 'summary') else ""
    
    return {
        "title": item.title or "Anime News",
        "synopsis": clean_summary,
        "imageUrl": final_image,
        "genres": ["News"],
        "score": None,
        "year": None,
        "studios": [],
        "episodes": None,
        "status": None,
        "animeName": item.title,
        "extraImages": []
    }
