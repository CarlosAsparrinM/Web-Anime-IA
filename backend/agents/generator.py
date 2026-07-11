import os
import json
import httpx
import re
import random
from slugify import slugify
from agents.prompts import get_editor_prompt, get_translator_prompt, get_reviewer_prompt
from agents.categories import get_category_for_today
from agents.tavily import fetch_tavily_research
from agents.strategies import get_strategy
from agents.llm import call_llm, get_reliable_images
import asyncio

async def _run_pipeline(category: str):
    strategy = get_strategy(category)
    source_data = None
    print("2. Fetching Raw Data from APIs...")
    try:
        source_data = await strategy.fetch_data()
    except Exception as e:
        print(f"Failed to fetch source data, falling back to random anime. {e}")
        from agents.sources import fetch_random_anime
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
            editor_response_raw = await call_llm(editor_prompt, "gemini:gemini-2.5-flash,cerebras:gemma-4-31b,groq:llama-3.1-8b-instant", 1500)
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
    search_query = strategy.get_tavily_query(clean_title, source_data)
        
    tavily_results, tavily_images = await fetch_tavily_research(search_query, category)
    
    all_facts = []
    if tavily_results and isinstance(tavily_results, list):
        for i, source in enumerate(tavily_results):
            print(f"- Mapping source {i+1}/{len(tavily_results)}: {source.get('title')}")
            map_prompt = get_researcher_map_prompt(category, editor_briefing.get("cleanTitle"), source, strategy.MAP_BLACKLIST_INSTRUCTION)
            try:
                map_res = await call_llm(map_prompt, "gemini:gemini-2.5-flash,cerebras:gemma-4-31b,groq:llama-3.1-8b-instant", 1000)
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
    reduce_prompt = get_researcher_reduce_prompt(category, editor_briefing.get("cleanTitle"), all_facts, source_data, strategy.REDUCE_JSON_FORMAT, strategy.REDUCE_EXTRA_INSTRUCTION)
    
    research_dossier = {}
    for attempt in range(3):
        try:
            reduce_res = await call_llm(reduce_prompt, "cerebras:gpt-oss-120b,groq:openai/gpt-oss-120b,gemini:gemini-2.5-flash", 2000)
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
            fact_checker_res = await call_llm(fact_checker_prompt, "cerebras:gpt-oss-120b,groq:openai/gpt-oss-120b,gemini:gemini-2.5-flash", 2000)
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
    # ITERATION 2.7: DOSSIER QUALITY GATE
    # ---------------------------------------------------------
    print("4.7. ITERATION 2.7: Dossier Quality Gate...")
    
    if not strategy.check_dossier_quality(research_dossier):
        raise ValueError(f"Dossier Quality Gate failed for '{clean_title}' in category '{category}'. Dossier is too thin to write a quality article.")

    # ---------------------------------------------------------
    # ITERATION 2.8: ARCHITECT AGENT (Dynamic Word Distribution)
    # ---------------------------------------------------------
    from agents.prompts import get_architect_prompt
    
    print("4.8. ITERATION 2.8: Calling Architect Agent...")
    
    outline = strategy.get_outline(research_dossier, editor_briefing.get("cleanTitle"))
    target_words = getattr(strategy, "TARGET_WORD_COUNT", 1000)
    
    architect_prompt = get_architect_prompt(category, editor_briefing.get("cleanTitle"), research_dossier, outline, target_words)
    
    architect_plan = []
    for attempt in range(3):
        try:
            architect_res = await call_llm(architect_prompt, "gemini:gemini-2.5-flash,cerebras:gemma-4-31b,groq:llama-3.1-8b-instant", 1000)
            json_match = re.search(r'\[[\s\S]*\]', architect_res)
            if json_match:
                architect_plan = json.loads(json_match.group(0))
                if isinstance(architect_plan, list) and len(architect_plan) == len(outline):
                    print("--> Architect successfully generated word distribution.")
                    break
            print(f"Architect returned invalid JSON format (attempt {attempt+1}/3). Retrying...")
            await asyncio.sleep(2)
        except Exception as e:
            print(f"Architect failed (attempt {attempt+1}/3): {e}")
            await asyncio.sleep(2)
            
    # Fallback to math division if Architect fails
    if not architect_plan or len(architect_plan) != len(outline):
        print("--> Architect failed after 3 attempts. Using fallback mathematical distribution.")
        per_section = target_words // len(outline)
        architect_plan = [{"title": title, "word_target": per_section} for title in outline]
        
    # Create a mapping for quick lookup in the writer phase
    word_targets_map = {item.get("title", ""): item.get("word_target", target_words // len(outline)) for item in architect_plan}

    # ---------------------------------------------------------
    # ITERATION 3: WRITER & REVIEWER (FEEDBACK LOOP)
    # ---------------------------------------------------------
    print("5. ITERATION 3: Calling Writer & Reviewer (Feedback Loop)...")
    
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
        
    final_reliable_images = await get_reliable_images(editor_briefing.get("cleanTitle"), source_data.get("extraImages", []), tavily_images)
    image_distribution = distribute_images(final_reliable_images, outline)
    
    spanish_markdown = ""
    
    # 1. Escritura Inicial
    print("\n--- WRITING INITIAL DRAFT ---")
    section_texts = [""] * len(outline)
    previous_summary = ""
    for i, section_title in enumerate(outline):
        current_target = word_targets_map.get(section_title, target_words // len(outline))
        print(f"- Writing section {i+1}/{len(outline)}: {section_title} (Target: ~{current_target} words)")
        section_images = image_distribution.get(i, [])
        section_prompt = get_section_writer_prompt(
            category, 
            section_title, 
            research_dossier, 
            section_images, 
            previous_summary,
            strategy.WRITER_WORD_COUNT_GUIDELINE,
            strategy.WRITER_SOURCE_INSTRUCTION,
            strategy.WRITER_DEDUCTION_INSTRUCTION,
            "",
            current_target
        )
        
        try:
            section_text = await call_llm(section_prompt, "cerebras:gpt-oss-120b,groq:llama-3.3-70b-versatile,gemini:gemini-2.5-flash", 2000)
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
        reviewer_res_raw = await call_llm(reviewer_prompt, "cerebras:gpt-oss-120b,groq:llama-3.3-70b-versatile,gemini:gemini-2.5-flash", 2000)
        
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
                    current_target = word_targets_map.get(section_title, target_words // len(outline))
                    section_prompt = get_section_writer_prompt(
                        category, 
                        section_title, 
                        research_dossier, 
                        section_images, 
                        temp_summary, 
                        strategy.WRITER_WORD_COUNT_GUIDELINE,
                        strategy.WRITER_SOURCE_INSTRUCTION,
                        strategy.WRITER_DEDUCTION_INSTRUCTION,
                        reviewer_feedback,
                        current_target
                    )
                    
                    try:
                        new_text = await call_llm(section_prompt, "cerebras:gpt-oss-120b,groq:llama-3.3-70b-versatile,gemini:gemini-2.5-flash", 2000)
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
            english_markdown = await call_llm(translator_prompt, "groq:llama-3.3-70b-versatile,cerebras:gemma-4-31b,gemini:gemini-2.5-flash", 8000)
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
            titulator_res_raw = await call_llm(titulator_prompt, "gemini:gemini-2.5-flash,cerebras:gemma-4-31b,groq:llama-3.1-8b-instant", 3000)
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
