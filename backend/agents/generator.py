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

async def _run_pipeline(category: str):
    source_data = None
    print("2. Fetching Raw Data from APIs...")
    try:
        if category == 'novedades':
            source_data = await fetch_anime_news()
        elif category == 'curiosidades':
            # Reintentar hasta encontrar un anime finalizado, con mínimo 3 episodios y del año 2025 o anterior
            for attempt in range(5):
                source_data = await fetch_random_anime()
                episodes = source_data.get("episodes")
                episodes_val = int(episodes) if (isinstance(episodes, (int, float)) or (isinstance(episodes, str) and episodes.isdigit())) else 0
                year = source_data.get("year")
                year_val = int(year) if (isinstance(year, (int, float)) or (isinstance(year, str) and year.isdigit())) else 0
                
                if (source_data.get("status") == "Finished Airing" and 
                    episodes_val >= 3 and 
                    year_val > 0 and year_val < 2026):
                    print(f"--> Selected valid anime for curiosidades: {source_data.get('title')} ({source_data.get('year')}, {source_data.get('episodes')} eps)")
                    break
                print(f"--> Anime '{source_data.get('title')}' skipped: status={source_data.get('status')}, eps={episodes_val}, year={year_val}. Retrying...")
        else: # analisis
            # Reintentar para encontrar un anime finalizado, con mínimo 3 episodios y del año 2025 o anterior
            for attempt in range(5):
                source_data = await fetch_top_anime()
                episodes = source_data.get("episodes")
                episodes_val = int(episodes) if (isinstance(episodes, (int, float)) or (isinstance(episodes, str) and episodes.isdigit())) else 0
                year = source_data.get("year")
                year_val = int(year) if (isinstance(year, (int, float)) or (isinstance(year, str) and year.isdigit())) else 0
                
                if (source_data.get("status") == "Finished Airing" and 
                    episodes_val >= 3 and 
                    year_val > 0 and year_val < 2026):
                    print(f"--> Selected valid anime for analisis: {source_data.get('title')} ({source_data.get('year')}, {source_data.get('episodes')} eps)")
                    break
                print(f"--> Anime '{source_data.get('title')}' skipped: status={source_data.get('status')}, eps={episodes_val}, year={year_val}. Retrying...")
    except Exception as e:
        print(f"Failed to fetch source data, falling back to random anime. {e}")
        try:
            for attempt in range(3):
                source_data = await fetch_random_anime()
                episodes = source_data.get("episodes")
                episodes_val = int(episodes) if (isinstance(episodes, (int, float)) or (isinstance(episodes, str) and episodes.isdigit())) else 0
                if source_data.get("status") == "Finished Airing" and episodes_val >= 3:
                    break
        except Exception as e2:
            print(f"Fallback fetch_random_anime also failed: {e2}. Using hardcoded dummy data.")
            source_data = {
                "title": "Neon Genesis Evangelion",
                "synopsis": "En el año 2015, el mundo está al borde de la destrucción...",
                "imageUrl": "https://images.unsplash.com/photo-1578632767115-351597cf2477?q=80&w=800&auto=format&fit=crop",
                "genres": ["Mecha", "Psychological", "Sci-Fi"],
                "score": 8.35,
                "year": 1995,
                "studios": ["Gainax", "Tatsunoko Production"],
                "episodes": 26,
                "status": "Finished Airing",
                "extraImages": []
            }

    raw_title = source_data.get('title')
    print(f"- Raw Title fetched: {raw_title}")

    # PRE-CHECK: Verificar duplicados con el título crudo antes de gastar tokens en el Editor
    from database import get_db
    db = get_db()
    if raw_title:
        existing_raw = await db["articles"].find_one({
            "animeName": raw_title,
            "category": category
        })
        if existing_raw:
            raise ValueError(f"An article for '{raw_title}' in category '{category}' already exists in the database.")

    # ---------------------------------------------------------
    # ITERATION 1: EDITOR
    # ---------------------------------------------------------
    print("3. ITERATION 1: Calling Editor Agent...")
    editor_prompt = get_editor_prompt(category, source_data)
    
    editor_briefing = {}
    for attempt in range(3):
        try:
            editor_response_raw = await call_llm(editor_prompt, "cerebras:gemma-4-31b,gemini:gemini-2.5-flash,groq:llama-3.1-8b-instant", 1500)
            json_match = re.search(r'\{[\s\S]*\}', editor_response_raw)
            if not json_match:
                raise ValueError("No JSON found")
            
            json_str = json_match.group(0)
            # Remover posibles comentarios (//) pero ignorar los de las URLs (http://)
            json_str = re.sub(r'(?<!:)//.*', '', json_str)
            
            editor_briefing = json.loads(json_str)
            break
        except Exception as e:
            if attempt == 2:
                print("Editor failed to return valid JSON after 3 attempts. Error:", e)
                raise Exception("Editor Pipeline Stage Failed")
            print(f"Editor failed (attempt {attempt+1}/3). Retrying... Error:", e)
            await asyncio.sleep(2)

    clean_title = editor_briefing.get('cleanTitle')
    print(f"- Editor Clean Title: {clean_title}")

    from database import get_db
    db = get_db()
    existing_article = await db["articles"].find_one({
        "animeName": clean_title,
        "category": category
    })
    if existing_article:
        raise ValueError(f"An article for '{clean_title}' in category '{category}' already exists in the database.")

    # ---------------------------------------------------------
    # ITERATION 2: RESEARCHER (MAP-REDUCE)
    # ---------------------------------------------------------
    from agents.prompts import get_researcher_map_prompt, get_researcher_reduce_prompt, get_fact_checker_prompt, get_section_writer_prompt, get_titulator_prompt, get_image_agent_prompt
    
    print("4. ITERATION 2: Calling Researcher Agent (MAP-REDUCE)...")
    if category == 'novedades':
        # Para novedades, usamos el título original de la noticia en vez del limpio
        raw_news_title = source_data.get('title', clean_title)
        search_query = f'"{raw_news_title}" anime latest news update official'
    elif category == 'curiosidades':
        search_query = f'{clean_title} anime trivia easter eggs hidden facts'
    else:
        search_query = f'{clean_title} anime plot characters animation review'
        
    tavily_results, tavily_images = await fetch_tavily_research(search_query, category)
    
    all_facts = []
    if tavily_results and isinstance(tavily_results, list):
        for i, source in enumerate(tavily_results):
            print(f"- Mapping source {i+1}/{len(tavily_results)}: {source.get('title')}")
            map_prompt = get_researcher_map_prompt(category, editor_briefing.get("cleanTitle"), source)
            try:
                map_res = await call_llm(map_prompt, "cerebras:gemma-4-31b,gemini:gemini-2.5-flash,groq:llama-3.1-8b-instant", 1000)
                json_match = re.search(r'\{[\s\S]*\}', map_res)
                if json_match:
                    all_facts.append(json.loads(json_match.group(0)))
            except Exception as e:
                print(f"Failed to map source {i+1}: {e}")
                
    # SHORT-CIRCUIT: Verificar si realmente se extrajo algún hecho
    has_any_facts = False
    for fact_group in all_facts:
        if fact_group.get("facts") and len(fact_group["facts"]) > 0:
            has_any_facts = True
            break
            
    if not has_any_facts:
        print("--> Short-circuit: 0 hechos extraídos de las fuentes. Abortando temprano para no gastar tokens en REDUCE y Fact-Checker.")
        raise ValueError("Fact-Checker flagged this anime as having insufficient data.")
    
    print("- Reducing facts into Master Dossier...")
    reduce_prompt = get_researcher_reduce_prompt(category, editor_briefing.get("cleanTitle"), all_facts)
    
    research_dossier = {}
    for attempt in range(3):
        try:
            reduce_res = await call_llm(reduce_prompt, "gemini:gemini-2.5-flash,cerebras:gemma-4-31b,groq:llama-3.1-8b-instant", 2000)
            json_match = re.search(r'\{[\s\S]*\}', reduce_res)
            if not json_match:
                raise ValueError("No JSON found")
                
            json_str = json_match.group(0)
            json_str = re.sub(r'(?<!:)//.*', '', json_str)
            research_dossier = json.loads(json_str)
            break
        except Exception as e:
            if attempt == 2:
                print("Researcher REDUCE failed JSON parse after 3 attempts, using fallback.", e)
                research_dossier = {"error": "Failed to parse researcher output", "raw": all_facts}
            else:
                print(f"Researcher REDUCE failed (attempt {attempt+1}/3). Retrying...")
                await asyncio.sleep(2)

    # ---------------------------------------------------------
    # ITERATION 2.5: FACT-CHECKER
    # ---------------------------------------------------------
    print("4.5. ITERATION 2.5: Calling Fact-Checker Agent...")
    fact_checker_prompt = get_fact_checker_prompt(category, editor_briefing.get("cleanTitle"), research_dossier, tavily_results)
    
    for attempt in range(3):
        try:
            fact_checker_res = await call_llm(fact_checker_prompt, "gemini:gemini-2.5-flash,cerebras:gemma-4-31b,groq:llama-3.1-8b-instant", 2000)
            json_match = re.search(r'\{[\s\S]*\}', fact_checker_res)
            if json_match:
                json_str = json_match.group(0)
                json_str = re.sub(r'(?<!:)//.*', '', json_str)
                research_dossier = json.loads(json_str)
            break
        except Exception as e:
            if attempt == 2:
                print("Fact-checker parse failed after 3 attempts.", e)
                break
            print(f"Fact-Checker failed (attempt {attempt+1}/3). Retrying...")
            await asyncio.sleep(2)
    if research_dossier.get("status") == "INSUFFICIENT_DATA":
        raise ValueError("Fact-Checker flagged this anime as having insufficient data.")
    print("- Fact-Checker successfully sanitized the Master Dossier.")

    # ---------------------------------------------------------
    # ITERATION 3: WRITER (Iterative Section by Section)
    # ---------------------------------------------------------
    # ---------------------------------------------------------
    # ITERATION 3: WRITER & REVIEWER (FEEDBACK LOOP)
    # ---------------------------------------------------------
    print("5. ITERATION 3: Calling Writer & Reviewer (Feedback Loop)...")
    
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
            return [f"Introducción y Premisa de {title}", "¿De qué trata?", "Personajes Clave", "Animación y Técnica", "Veredicto Final"]

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
    
    final_reliable_images = await get_reliable_images(editor_briefing.get("cleanTitle"), source_data.get("extraImages", []), tavily_images)
    image_distribution = distribute_images(final_reliable_images, outline)
    
    spanish_markdown = ""
    
    # 1. Escritura Inicial
    print("\n--- WRITING INITIAL DRAFT ---")
    section_texts = [""] * len(outline)
    previous_summary = ""
    for i, section_title in enumerate(outline):
        print(f"- Writing section {i+1}/{len(outline)}: {section_title}")
        section_images = image_distribution.get(i, [])
        section_prompt = get_section_writer_prompt(category, section_title, research_dossier, section_images, previous_summary, "")
        
        try:
            section_text = await call_llm(section_prompt, "groq:llama-3.3-70b-versatile,gemini:gemini-2.5-pro,cerebras:gpt-oss-120b", 2000)
            section_texts[i] = section_text
            previous_summary += f"### {section_title}\n{section_text}\n\n"
        except Exception as e:
            print(f"Failed to write section {section_title}: {e}")
            
    spanish_markdown = "\n\n".join(section_texts)

    # 2. Bucle de Revisión y Corrección Quirúrgica
    for attempt in range(3):
        print(f"\n--- REVIEW LOOP ATTEMPT {attempt + 1}/3 ---")
        print("- Calling Reviewer Agent...")
        
        # Pasamos el outline al Revisor
        reviewer_prompt = get_reviewer_prompt(category, spanish_markdown, editor_briefing, research_dossier, outline)
        reviewer_res_raw = await call_llm(reviewer_prompt, "groq:llama-3.3-70b-versatile,gemini:gemini-2.5-pro,cerebras:gpt-oss-120b", 2000)
        
        needs_revision = False
        sections_to_fix = []
        try:
            json_match = re.search(r'\{[\s\S]*\}', reviewer_res_raw)
            if json_match:
                review_data = json.loads(json_match.group(0))
                if review_data.get("status") == "APPROVED":
                    print("--> APPROVED BY REVIEWER!")
                    break
                else:
                    reviewer_feedback = review_data.get("feedback", "El artículo necesita ser reescrito.")
                    sections_to_fix = review_data.get("sections_to_fix", list(range(1, len(outline) + 1)))
                    print(f"--> NEEDS REVISION on sections {sections_to_fix}: {reviewer_feedback}")
                    needs_revision = True
            else:
                print("--> Reviewer failed to return JSON, forcing approval to avoid infinite loop.")
                break
        except Exception as e:
            print(f"--> Reviewer parse error: {e}. Forcing approval.")
            break
            
        if needs_revision and attempt < 2:
            print("- Rewriting problematic sections...")
            for sec_idx in sections_to_fix:
                idx = sec_idx - 1
                if 0 <= idx < len(outline):
                    section_title = outline[idx]
                    print(f"  -> Rewriting section {sec_idx}: {section_title}")
                    
                    # Reconstruir previous_summary hasta esta sección con el texto real
                    temp_summary = ""
                    for j in range(idx):
                        temp_summary += f"### {outline[j]}\n{section_texts[j]}\n\n"
                        
                    section_images = image_distribution.get(idx, [])
                    section_prompt = get_section_writer_prompt(category, section_title, research_dossier, section_images, temp_summary, reviewer_feedback)
                    
                    try:
                        new_text = await call_llm(section_prompt, "groq:llama-3.3-70b-versatile,gemini:gemini-2.5-pro,cerebras:gpt-oss-120b", 2000)
                        if new_text:
                            section_texts[idx] = new_text
                    except Exception as e:
                        print(f"  -> Failed to rewrite section {section_title}: {e}")
            
            # Re-ensamblar el artículo con las secciones corregidas
            spanish_markdown = "\n\n".join(section_texts)

    # ---------------------------------------------------------
    # ITERATION 4: TRANSLATOR (English Only)
    # ---------------------------------------------------------
    print("6. ITERATION 4: Calling Translator Agent (English Only)...")
    translator_prompt = get_translator_prompt(spanish_markdown)
    english_markdown = ""
    for attempt in range(3):
        try:
            english_markdown = await call_llm(translator_prompt, "cerebras:gemma-4-31b,gemini:gemini-2.5-flash,groq:llama-3.1-8b-instant", 8000)
            if not english_markdown:
                raise ValueError("Empty translation received from LLM")
            break
        except Exception as e:
            if attempt == 2:
                print(f"Translator failed after 3 attempts: {e}")
                raise Exception(f"Pipeline aborted: Translator phase failed. {e}")
            print(f"Translator failed (attempt {attempt+1}/3). Retrying...")
            await asyncio.sleep(2)

    # ---------------------------------------------------------
    # ITERATION 5: IMAGE QA (HTTP Validation)
    # ---------------------------------------------------------
    print("7. ITERATION 5: Validating Images via HTTP...")
    image_urls_in_md = re.findall(r'!\[.*?\]\((.*?)\)', spanish_markdown)
    
    if image_urls_in_md:
        async with httpx.AsyncClient(timeout=10.0) as img_client:
            for url in image_urls_in_md:
                is_valid = False
                try:
                    img_res = await img_client.get(url, follow_redirects=True)
                    if img_res.status_code == 200:
                        is_valid = True
                except Exception as e:
                    print(f"- Image QA: Error checking URL {url}: {e}")
                
                if not is_valid:
                    print(f"- Image QA: Flagged URL for replacement (HTTP check failed): {url}")
                    try:
                        def search_ddgs():
                            from ddgs import DDGS
                            with DDGS() as ddgs:
                                return ddgs.images(f"{editor_briefing.get('cleanTitle')} anime official scene", max_results=2)
                        
                        ddgs_res = await asyncio.to_thread(search_ddgs)
                        if ddgs_res:
                            new_url = ddgs_res[0].get("image")
                            spanish_markdown = spanish_markdown.replace(url, new_url)
                            english_markdown = english_markdown.replace(url, new_url)
                            print(f"  -> Replaced with: {new_url}")
                    except Exception as ddgs_e:
                        print(f"  -> DDGS search failed, leaving original. {ddgs_e}")
                else:
                    print(f"- Image QA: URL is valid: {url}")

    # ---------------------------------------------------------
    # ITERATION 6: TITULATOR
    # ---------------------------------------------------------
    print("8. ITERATION 6: Calling Titulator Agent...")
    titulator_prompt = get_titulator_prompt(spanish_markdown, english_markdown, editor_briefing)
    
    parsed_response = {}
    for attempt in range(3):
        try:
            titulator_res_raw = await call_llm(titulator_prompt, "cerebras:gemma-4-31b,gemini:gemini-2.5-flash,groq:llama-3.1-8b-instant", 3000)
            json_match = re.search(r'\{[\s\S]*\}', titulator_res_raw)
            if not json_match:
                raise ValueError("No JSON found")
            json_str = json_match.group(0)
            json_str = re.sub(r',\s*([\]}])', r'\1', json_str)
            json_str = json_str.replace("\\'", "'")
            parsed_response = json.loads(json_str)
            break
        except Exception as e:
            if attempt == 2:
                print(f"Titulator parse failed after 3 attempts.", e)
                raise Exception(f"Pipeline aborted: Titulator phase failed. {e}")
            print(f"Titulator failed (attempt {attempt+1}/3). Retrying...")
            await asyncio.sleep(2)

    print("9. Pipeline Completed Successfully. Formatting DB Object...")

    title_es = parsed_response.get("title_es", "Título por defecto")
    slug = slugify(title_es) + '-' + str(random.randint(100, 999))
    final_cover_image = source_data.get("imageUrl")
    
    if "unsplash.com" in final_cover_image and final_reliable_images:
        final_cover_image = final_reliable_images[0]

    return {
        "title": {
            "es": title_es,
            "en": parsed_response.get("title_en") or title_es,
        },
        "slug": slug,
        "content": {
            "es": spanish_markdown,
            "en": english_markdown,
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


async def generate_article(force_category: str = None):
    print("1. Starting Multi-Agent Generation Pipeline (5 Phases)")
    category = force_category or get_category_for_today()
    print(f"- Selected Category: {category}")

    for attempt in range(1, 4):
        print(f"\n--- PIPELINE ATTEMPT {attempt}/3 ---")
        try:
            article_data = await _run_pipeline(category)
            return article_data
        except Exception as e:
            if attempt == 3:
                print(f"Pipeline failed catastrophically after 3 attempts. Last error: {e}")
                raise e
            print(f"Pipeline attempt {attempt} failed: {e}. Retrying with a different anime/news in 2s...")
            await asyncio.sleep(2)
