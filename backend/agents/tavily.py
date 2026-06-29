import os
import httpx

async def fetch_tavily_research(query: str, category: str = "analisis") -> str:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        print("TAVILY_API_KEY no está configurada. Saltando investigación web real.")
        return "No hay datos de internet disponibles (Falta API Key)."

    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "include_answer": False,
        "max_results": 3
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
                return "Error al buscar información en internet."

            data = response.json()
            results = data.get('results', [])
            
            if not results:
                return "No se encontró información en internet sobre esto."

            combined_content = "\n".join(
                [f"Fuente: {r.get('title')}\nContenido: {r.get('content')}\n---" for r in results]
            )

            return combined_content
    except Exception as e:
        print(f"Fallo inesperado al consultar Tavily: {e}")
        return "Error de red al investigar."
