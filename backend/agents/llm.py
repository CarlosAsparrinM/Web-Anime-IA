import os
import json
import httpx
import asyncio

async def get_reliable_images(title: str, source_images: list, tavily_images: list) -> list:
    valid_images = [img for img in source_images if img]
    if len(valid_images) >= 5:
        return valid_images[:5]
        
    if tavily_images:
        for img in tavily_images:
            if img and img.endswith(('.jpg', '.png', '.jpeg', '.webp', '.gif')) and img not in valid_images:
                valid_images.append(img)
        if len(valid_images) >= 5:
            return valid_images[:5]

    print("Nivel 3: Buscando imágenes en DuckDuckGo...")
    try:
        def search_images():
            from ddgs import DDGS
            with DDGS() as ddgs:
                return ddgs.images(f"{title} anime official art wallpaper", max_results=5)
                
        results = await asyncio.to_thread(search_images)
        if results:
            for r in results:
                img = r.get("image")
                if img and img not in valid_images:
                    valid_images.append(img)
    except Exception as e:
        print(f"Fallo en DuckDuckGo: {e}")

    if not valid_images:
        valid_images = [
            "https://images.unsplash.com/photo-1578632767115-351597cf2477?q=80&w=800&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?q=80&w=800&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1580477655122-540c493a3885?q=80&w=800&auto=format&fit=crop"
        ]

    return valid_images[:5]

async def call_llm(prompt_json_string: str, model_str: str, max_tokens: int = 8000, max_retries: int = 3) -> str:
    api_url = os.getenv("API_ONE_URL", "http://localhost:3000")
    api_key = os.getenv("API_ONE_KEY")

    if not api_key:
        raise ValueError("Missing API_ONE_KEY in environment variables")

    messages = json.loads(prompt_json_string)

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{api_url}/v1/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {api_key}"
                    },
                    json={
                        "model": model_str,
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": max_tokens
                    }
                )

                if response.status_code != 200:
                    raise Exception(f"API-One failed with status {response.status_code}: {response.text}")

                ai_result = response.json()
                if not ai_result.get("choices") or len(ai_result["choices"]) == 0:
                    raise Exception("API-One returned empty choices array")

                message = ai_result["choices"][0]["message"]
                
                # Throttling para proteger cuotas gratuitas (Rate Limits)
                await asyncio.sleep(7)

                if "content" not in message:
                    if message.get("refusal"):
                        raise Exception(f"LLM Refusal: {message.get('refusal')}")
                    return ""
                
                return message["content"] or ""
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"Call to LLM failed after {max_retries} attempts. Last error: {e}")
                raise e
            
            backoff_time = 10 * (2 ** attempt)
            print(f"LLM call failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {backoff_time}s...")
            await asyncio.sleep(backoff_time)
