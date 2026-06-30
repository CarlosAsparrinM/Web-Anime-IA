import os
import json
import httpx
import re
import random
from slugify import slugify
from agents.sources import fetch_random_anime, fetch_seasonal_anime, fetch_top_anime, fetch_anime_news
from agents.prompts import get_editor_prompt, get_researcher_prompt, get_writer_prompt, get_translator_prompt, get_reviewer_prompt
from agents.categories import get_category_for_today
from agents.tavily import fetch_tavily_research

async def call_llm(prompt_json_string: str, max_tokens: int = 8000) -> str:
    api_url = os.getenv("API_ONE_URL", "http://localhost:3000")
    api_key = os.getenv("API_ONE_KEY")

    if not api_key:
        raise ValueError("Missing API_ONE_KEY in environment variables")

    messages = json.loads(prompt_json_string)

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
            raise Exception(f"API-One failed: {response.text}")

        ai_result = response.json()
        if not ai_result.get("choices") or len(ai_result["choices"]) == 0:
            raise Exception("API-One returned empty choices array")

        return ai_result["choices"][0]["message"]["content"]

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
    # ITERATION 2: RESEARCHER
    # ---------------------------------------------------------
    print("4. ITERATION 2: Calling Researcher Agent (Tavily)...")
    if category == 'novedades':
        search_query = f"{editor_briefing.get('cleanTitle')} anime latest news update announcements site:animenewsnetwork.com OR site:crunchyroll.com/news OR site:reddit.com/r/anime OR site:myanimelist.net/news OR site:comicbook.com/anime OR site:sportskeeda.com/anime"
    elif category == 'curiosidades':
        search_query = f"{editor_briefing.get('cleanTitle')} anime trivia easter eggs hidden facts"
    else:
        search_query = f"{editor_briefing.get('cleanTitle')} anime plot characters animation review"
        
    tavily_data = await fetch_tavily_research(search_query, category)
    
    researcher_prompt = get_researcher_prompt(category, editor_briefing.get("cleanTitle"), tavily_data)
    researcher_response_raw = await call_llm(researcher_prompt, 1500)
    
    try:
        json_match = re.search(r'\{[\s\S]*\}', researcher_response_raw)
        if not json_match:
            raise ValueError("No JSON found")
        research_dossier = json.loads(json_match.group(0))
    except Exception as e:
        print("Researcher failed JSON parse, using fallback.", researcher_response_raw)
        research_dossier = {"error": "Failed to parse researcher output", "raw": tavily_data}

    # ---------------------------------------------------------
    # ITERATION 3: WRITER (Spanish Only)
    # ---------------------------------------------------------
    print("5. ITERATION 3: Calling Writer Agent (Spanish Only)...")
    writer_prompt = get_writer_prompt(category, editor_briefing, source_data, research_dossier)
    spanish_markdown = await call_llm(writer_prompt, 8000)
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
