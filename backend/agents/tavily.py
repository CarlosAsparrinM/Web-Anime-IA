import os
import httpx

async def fetch_tavily_research(query: str, category: str = "analisis") -> list:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        print("TAVILY_API_KEY no está configurada. Saltando investigación web real.")
        return [], []

    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "include_answer": False,
        "include_raw_content": True, # Extrae todo el texto de la web, no solo un resumen
        "include_images": True,
        "max_results": 7 # Límite ideal para el plan Free (5-10)
    }

    # Time-awareness para noticias
    if category == "novedades":
        payload["topic"] = "news"
        payload["days"] = 3 # Solo leer contenido de los últimos 3 días

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                'https://api.tavily.com/search',
                json=payload,
                timeout=30.0
            )
            
            if response.status_code != 200:
                print(f"Error en Tavily API: {response.text}")
                return [], []

            data = response.json()
            results = data.get('results', [])
            images = data.get('images', [])
            
            return results, images
    except Exception as e:
        print(f"Fallo inesperado al consultar Tavily: {e}")
        return [], []
