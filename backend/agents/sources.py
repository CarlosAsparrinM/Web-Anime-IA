import httpx
import random
import feedparser
import asyncio
import re

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
        "year": anime.get("year")
    }

async def fetch_random_anime() -> dict:
    page = random.randint(1, 50)
    async with httpx.AsyncClient() as client:
        res = await client.get(f"https://api.jikan.moe/v4/anime?order_by=score&sort=desc&page={page}", timeout=10.0)
        data = res.json()
        index = random.randint(0, len(data["data"]) - 1)
        anime = data["data"][index]
        formatted = format_jikan_data(anime)
        formatted["extraImages"] = await get_extra_images(anime["mal_id"])
        return formatted

async def fetch_seasonal_anime() -> dict:
    async with httpx.AsyncClient() as client:
        res = await client.get("https://api.jikan.moe/v4/seasons/now", timeout=10.0)
        data = res.json()
        index = random.randint(0, len(data["data"]) - 1)
        anime = data["data"][index]
        formatted = format_jikan_data(anime)
        formatted["extraImages"] = await get_extra_images(anime["mal_id"])
        return formatted

async def fetch_top_anime() -> dict:
    page = random.randint(1, 5)
    async with httpx.AsyncClient() as client:
        res = await client.get(f"https://api.jikan.moe/v4/top/anime?page={page}", timeout=10.0)
        data = res.json()
        index = random.randint(0, len(data["data"]) - 1)
        anime = data["data"][index]
        formatted = format_jikan_data(anime)
        formatted["extraImages"] = await get_extra_images(anime["mal_id"])
        return formatted

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
        "animeName": item.title,
        "extraImages": []
    }
