import httpx
import asyncio

async def generate_category(category):
    print(f"[{category.upper()}] Comenzando generación...")
    url = f"http://localhost:8000/api/generate?secret=mi-secreto-local-123&force=true&category={category}"
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            response = await client.get(url)
            if response.status_code == 201:
                data = response.json()
                print(f"[{category.upper()}] ÉXITO! Artículo guardado en BD: {data['article']['title']['es']}")
            else:
                print(f"[{category.upper()}] FALLO con status {response.status_code}: {response.text}")
        except Exception as e:
            print(f"[{category.upper()}] ERROR DE RED: {e}")

async def main():
    categories = ['analisis', 'novedades', 'curiosidades']
    # Ejecutar en serie para no saturar las cuotas de LLMs o rate limits
    for cat in categories:
        await generate_category(cat)
        print("-" * 50)
        
if __name__ == '__main__':
    asyncio.run(main())
