import os
import json
import httpx
import re
import random
from slugify import slugify
from agents.sources import fetch_random_anime, fetch_seasonal_anime, fetch_top_anime, fetch_anime_news
from agents.prompts import get_editor_prompt, get_translator_prompt, get_reviewer_prompt
from agents.categories import get_category_for_today
from agents.tavily import fetch_tavily_research

import asyncio

async def call_llm(prompt_json_string: str, max_tokens: int = 8000, max_retries: int = 3) -> str:
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
                        "model": "api-fallback",
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

                return ai_result["choices"][0]["message"]["content"]
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"Call to LLM failed after {max_retries} attempts. Last error: {e}")
                raise e
            
            backoff_time = 2 ** attempt
            print(f"LLM call failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {backoff_time}s...")
            await asyncio.sleep(backoff_time)

async def generate_article(force_category: str = None):
    print("1. Starting Multi-Agent Generation Pipeline (5 Phases)")
    category = force_category or get_category_for_today()
    source_data = None

    print(f"- Selected Category: {category}")
    print("2. Fetching Raw Data from APIs...")
    try:
        if category == 'novedades':
            source_data = await fetch_anime_news()
        elif category == 'curiosidades':
            source_data = await fetch_random_anime()
        else: # analisis
            source_data = await fetch_top_anime() if random.random() > 0.5 else await fetch_seasonal_anime()
    except Exception as e:
        print(f"Failed to fetch source data, falling back to random anime. {e}")
        source_data = await fetch_random_anime()

    print(f"- Raw Title fetched: {source_data.get('title')}")

    # ---------------------------------------------------------
    # ITERATION 1: EDITOR
    # ---------------------------------------------------------
    print("3. ITERATION 1: Calling Editor Agent...")
    editor_prompt = get_editor_prompt(category, source_data)
    editor_response_raw = await call_llm(editor_prompt, 1500)
    
    try:
        json_match = re.search(r'\{[\s\S]*\}', editor_response_raw)
        if not json_match:
            raise ValueError("No JSON found")
        editor_briefing = json.loads(json_match.group(0))
    except Exception as e:
        print("Editor failed to return valid JSON. Raw output:", editor_response_raw)
        raise Exception("Editor Pipeline Stage Failed")

    print(f"- Editor Clean Title: {editor_briefing.get('cleanTitle')}")

    # ---------------------------------------------------------
    # ITERATION 2: RESEARCHER (MAP-REDUCE)
    # ---------------------------------------------------------
    from agents.prompts import get_researcher_map_prompt, get_researcher_reduce_prompt, get_section_writer_prompt
    
    print("4. ITERATION 2: Calling Researcher Agent (MAP-REDUCE)...")
    if category == 'novedades':
        search_query = f"{editor_briefing.get('cleanTitle')} anime latest news update announcements site:animenewsnetwork.com OR site:crunchyroll.com/news OR site:reddit.com/r/anime OR site:myanimelist.net/news OR site:comicbook.com/anime OR site:sportskeeda.com/anime"
    elif category == 'curiosidades':
        search_query = f"{editor_briefing.get('cleanTitle')} anime trivia easter eggs hidden facts"
    else:
        search_query = f"{editor_briefing.get('cleanTitle')} anime plot characters animation review"
        
    tavily_results = await fetch_tavily_research(search_query, category)
    
    all_facts = []
    if tavily_results and isinstance(tavily_results, list):
        for i, source in enumerate(tavily_results):
            print(f"- Mapping source {i+1}/{len(tavily_results)}: {source.get('title')}")
            map_prompt = get_researcher_map_prompt(category, editor_briefing.get("cleanTitle"), source)
            try:
                map_res = await call_llm(map_prompt, 1000)
                json_match = re.search(r'\{[\s\S]*\}', map_res)
                if json_match:
                    all_facts.append(json.loads(json_match.group(0)))
            except Exception as e:
                print(f"Failed to map source {i+1}: {e}")
    
    print("- Reducing facts into Master Dossier...")
    reduce_prompt = get_researcher_reduce_prompt(category, editor_briefing.get("cleanTitle"), all_facts)
    reduce_res = await call_llm(reduce_prompt, 2000)
    
    try:
        json_match = re.search(r'\{[\s\S]*\}', reduce_res)
        if not json_match:
            raise ValueError("No JSON found")
        research_dossier = json.loads(json_match.group(0))
    except Exception as e:
        print("Researcher REDUCE failed JSON parse, using fallback.", reduce_res)
        research_dossier = {"error": "Failed to parse researcher output", "raw": all_facts}

    # ---------------------------------------------------------
    # ITERATION 3: WRITER (Iterative Section by Section)
    # ---------------------------------------------------------
    print("5. ITERATION 3: Calling Writer Agent (Iterative)...")
    
    def get_outline_for_category(cat: str, dos: dict, title: str) -> list:
        if cat == 'curiosidades':
            trivia_list = dos.get("triviaList", [])
            num_items = len(trivia_list) if trivia_list else 5
            out = [f"Introducción: {num_items} Cosas que no sabías de {title}"]
            for j in range(1, num_items + 1):
                out.append(f"Curiosidad #{j}")
            return out
        elif cat == 'novedades':
            return ["Titular y Resumen de la Noticia", "El Anuncio a Fondo", "Contexto del Anime"]
        else:
            return [f"Introducción y Análisis de {title}", "¿De qué trata?", "Personajes Clave", "Animación y Técnica", "Veredicto Final"]

    def distribute_images(sel_imgs: list, out: list) -> dict:
        img_map = {}
        idx = 0
        for j in range(1, len(out), 2):
            if idx < len(sel_imgs):
                img_map[j] = [sel_imgs[idx]]
                idx += 1
        for j in range(1, len(out)):
            if idx < len(sel_imgs) and j not in img_map:
                img_map[j] = [sel_imgs[idx]]
                idx += 1
        return img_map
        
    outline = get_outline_for_category(category, research_dossier, editor_briefing.get("cleanTitle"))
    image_distribution = distribute_images(editor_briefing.get("selectedImages", []), outline)
    
    spanish_markdown = ""
    previous_summary = ""
    
    for i, section_title in enumerate(outline):
        print(f"- Writing section {i+1}/{len(outline)}: {section_title}")
        section_images = image_distribution.get(i, [])
        section_prompt = get_section_writer_prompt(category, section_title, research_dossier, section_images, previous_summary)
        
        try:
            section_text = await call_llm(section_prompt, 2000)
            spanish_markdown += section_text + "\n\n"
            previous_summary += f"- Sección '{section_title}' ya redactada.\n"
        except Exception as e:
            print(f"Failed to write section {section_title}: {e}")
            
    print(f"- Writer generated {len(spanish_markdown)} characters of Spanish Markdown.")

    # ---------------------------------------------------------
    # ITERATION 4: TRANSLATOR (English Only)
    # ---------------------------------------------------------
    print("6. ITERATION 4: Calling Translator Agent (English Only)...")
    translator_prompt = get_translator_prompt(spanish_markdown)
    english_markdown = await call_llm(translator_prompt, 8000)
    print(f"- Translator generated {len(english_markdown)} characters of English Markdown.")

    # ---------------------------------------------------------
    # ITERATION 5: REVIEWER
    # ---------------------------------------------------------
    print("7. ITERATION 5: Calling Reviewer Agent...")
    reviewer_prompt = get_reviewer_prompt(spanish_markdown, english_markdown, editor_briefing)
    reviewer_response_raw = await call_llm(reviewer_prompt, 8000)
    
    try:
        json_match = re.search(r'\{[\s\S]*\}', reviewer_response_raw)
        if not json_match:
            raise ValueError("No JSON found")
        json_str = json_match.group(0)
        json_str = re.sub(r',\s*([\]}])', r'\1', json_str)
        json_str = json_str.replace("\\'", "'")
        parsed_response = json.loads(json_str)
    except Exception as e:
        print("Reviewer JSON Parse failed, attempting strict sanitization...", e)
        json_match2 = re.search(r'\{[\s\S]*\}', reviewer_response_raw)
        clean_str = json_match2.group(0) if json_match2 else reviewer_response_raw
        clean_str = re.sub(r'[\u0000-\u001F]+', " ", clean_str)
        clean_str = clean_str.replace("\\'", "'")
        try:
            parsed_response = json.loads(clean_str)
        except Exception as e2:
            print("Final JSON Parse failed. Raw Output:", reviewer_response_raw)
            raise Exception("Reviewer Pipeline Stage Failed - Bad JSON Format")

    print("8. Pipeline Completed Successfully. Formatting DB Object...")

    title_es = parsed_response.get("title_es", "Título por defecto")
    slug = slugify(title_es) + '-' + str(random.randint(100, 999))
    final_cover_image = source_data.get("imageUrl")

    return {
        "title": {
            "es": title_es,
            "en": parsed_response.get("title_en") or title_es,
        },
        "slug": slug,
        "content": {
            "es": parsed_response.get("content_es", "").replace("\\n", "\n"),
            "en": parsed_response.get("content_en", parsed_response.get("content_es", "")).replace("\\n", "\n"),
        },
        "excerpt": {
            "es": parsed_response.get("excerpt_es", "Sinopsis breve del artículo."),
            "en": parsed_response.get("excerpt_en", "Brief article summary."),
        },
        "category": category,
        "imageUrl": final_cover_image,
        "imageAlt": parsed_response.get("imageAlt") or editor_briefing.get("cleanTitle"),
        "animeName": editor_briefing.get("cleanTitle"),
        "tags": parsed_response.get("tags", []),
        "published": True
    }
