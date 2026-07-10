import json
from datetime import datetime

def get_editor_prompt(category: str, data: dict) -> str:
    images_context = "Imágenes disponibles: Ninguna"
    if data.get("extraImages"):
        images_context = "Imágenes disponibles:\n" + "\n".join([f"- {img}" for img in data["extraImages"]])

    system = """
Eres el Editor en Jefe de KenkoAnime. Tu trabajo es recibir datos crudos de una API de anime y "limpiarlos" para el equipo de redacción.
El nombre que viene de la API a veces tiene subtítulos técnicos molestos (ej. "(TV)", "(Dub)", "Part 1"). Debes limpiar esa basura técnica, PERO si el título indica una Temporada específica (ej. "Season 3") o una Película, DEBES mantener esa información en el título para que el artículo trate sobre esa temporada o película exacta y no generalice toda la franquicia.
Debes devolver ESTRICTAMENTE un objeto JSON con el siguiente formato:
{
  "cleanTitle": "Nombre limpio de la franquicia o título con sentido",
  "topicFocus": "Instrucción estricta para el escritor sobre qué enfoque darle (ej. Si la categoría es CURIOSIDADES, ordénale centrarse SOLO en listar secretos y easter eggs).",
  "selectedImages": ["url1", "url2", "url3"] // Selecciona hasta 3 o 4 imágenes, si hay disponibles, que tengan sentido
}
"""
    user = f"""
CATEGORÍA DEL ARTÍCULO: {category.upper()}
DATOS CRUDOS E INMUTABLES (HARD FACTS):
Título Original: {data.get("title")}
Sinopsis: {data.get("synopsis")}
Estudios: {", ".join(data.get("studios", [])) or "Desconocido"}
Episodios: {data.get("episodes", "N/A")}
Estado: {data.get("status", "N/A")}
Año: {data.get("year", "N/A")}
Géneros: {", ".join(data.get("genres", [])) or "Varios"}
Calificación (MyAnimeList): {data.get("score", "N/A")}/10
{images_context}

Genera el JSON del Briefing:
"""
    return json.dumps([{"role": "system", "content": system}, {"role": "user", "content": user}])


def get_researcher_map_prompt(category: str, clean_title: str, single_source: dict) -> str:
    blacklist_instruction = ""
    if category == 'novedades':
        blacklist_instruction = """CRÍTICO - LISTA NEGRA: Descarta INMEDIATAMENTE cualquier dato que:
- Provenga de Instagram, TikTok, Reddit, Twitter, YouTube.
- Sea una opinión, especulación o teoría de fans.
- Mencione seguidores, likes, views, posts, stories, hashtags.
- Mencione rumores, leaks, merchandising, cosplay o fanarts.
- Contenga frases como "podría", "se espera", "los fans creen"."""
    else:
        blacklist_instruction = """CRÍTICO - LISTA NEGRA: Descarta INMEDIATAMENTE cualquier dato que:
- Provenga de Instagram, TikTok, Reddit, Twitter, YouTube.
- Mencione seguidores, likes, views, posts, stories, hashtags.
- Mencione cosplay, fanarts o merchandising de nicho sin valor informativo.
NOTA: Para análisis y curiosidades, SÍ debes extraer análisis temáticos de la trama, conceptos filosóficos de la obra, recepción crítica, detalles de producción, impacto cultural e interpretaciones oficiales ampliamente aceptadas."""

    system = f"""
Eres un Asistente de Investigación (Fase MAP).
Tu trabajo es leer el texto extraído de una ÚNICA página web y extraer hechos, datos, personajes, análisis temático y citas útiles sobre el anime indicado, ignorando la basura de la web.

CRÍTICO: Extrae hechos ALTAMENTE ESPECÍFICOS. Evita generalizaciones vacías como "tiene personajes diversos" o "la animación es buena". En su lugar, extrae nombres y apellidos completos de personajes, relaciones de parentesco, habilidades específicas, nombres de estudios de animación, directores, compositores, cadenas de televisión de emisión reales (ej. BS11, Tokyo MX), bandas de opening/ending, y terminología técnica exacta si se menciona de forma verídica.

{blacklist_instruction}

Devuelve ESTRICTAMENTE un objeto JSON con este formato asignando un nivel de confianza y la fuente origen (título de la web):
{{
  "facts": [
    {{
      "fact": "Dato o hecho extraído detallado",
      "confidence": "HIGH | MEDIUM | LOW",
      "source": "Nombre de la fuente"
    }}
  ]
}}
"""
    user = f"""
CATEGORÍA: {category.upper()}
ANIME: {clean_title}

FUENTE: {single_source.get('title')}
CONTENIDO:
{str(single_source.get('raw_content') or single_source.get('content'))[:10000]}

Extrae los hechos relevantes para el anime y categoría en el JSON solicitado:
"""
    return json.dumps([{"role": "system", "content": system}, {"role": "user", "content": user}])


def get_researcher_reduce_prompt(category: str, clean_title: str, all_mapped_facts: list) -> str:
    today_date = datetime.now().strftime("%Y-%m-%d")
    
    if category == 'novedades':
        json_format = """{
  "headline": "¿Qué ocurrió exactamente?",
  "whoAnnounced": "¿Quién lo anunció oficialmente?",
  "when": "Fecha del anuncio",
  "where": "Fuente oficial",
  "whyItMatters": "¿Por qué es importante?",
  "whatChanges": "¿Qué cambia respecto a antes?",
  "context": "Contexto del anime para nuevos lectores",
  "verifiedFacts": ["Dato verificado 1", "Dato verificado 2"]
}"""
        extra_instruction = f"HOY ES {today_date}. Esta es una noticia de ÚLTIMA HORA. NO conviertas rumores en hechos ni expectativas en anuncios. NO uses 'los fans esperan...' sin declaración oficial."
    elif category == 'curiosidades':
        json_format = """{
  "triviaList": [
    {
      "fact": "Curiosidad única y específica (ej. censura, referencias, cambios)",
      "context": "Contexto detallado de la curiosidad",
      "source": "Fuente original"
    }
  ]
}"""
        extra_instruction = "AGRUPA Y FILTRA: No repitas el mismo dato de producción varias veces. Busca curiosidades DIVERSAS: cambios entre manga y anime, inspiraciones del autor, censura, referencias, cameos, récords. Si solo hay 3 curiosidades DIVERSAS reales en las fuentes, devuelve solo 3, no inventes relleno para llegar a más."
    else: # analisis
        json_format = """{
  "officialSynopsis": "Resumen fiel de la trama",
  "production": { "studio": "", "director": "", "writer": "", "composer": "", "year": "" },
  "themes": ["Tema 1", "Tema 2", "Tema 3"],
  "characters": [{ "name": "", "role": "", "traits": "" }],
  "worldBuilding": ["Detalle 1", "Detalle 2"],
  "lore": ["Secreto 1", "Mito 2"],
  "criticalReception": ["Recepción 1"],
  "interestingFacts": ["Producción secreta"]
}"""
        extra_instruction = "Construye un dossier enciclopédico sumamente rico, denso y profundo. Agrupa todos los personajes con sus nombres y apellidos correctos, roles y habilidades que vengan en las fuentes. Conserva detalles de producción muy precisos (estudios reales, directores, compositores, canales de emisión). Si los hechos contienen múltiples nombres de personajes o detalles de la trama, regístralos detalladamente sin omitir nada. Evita resúmenes genéricos."

    confidence_rule = 'Acepta hechos que vengan marcados con confidence: "HIGH" o "MEDIUM". Descarta los LOW (que son solo ruido de la web o comentarios irrelevantes).'

    system = f"""
Eres el Investigador Principal (Fase REDUCE).
Has recibido una lista de hechos extraídos de múltiples fuentes web sobre el anime.
Tu trabajo es consolidarlos, eliminar duplicados y devolver un "Dossier Maestro" estructurado.
CRÍTICO: {confidence_rule}
{extra_instruction}

CRÍTICO:
Debes devolver ESTRICTAMENTE un objeto JSON con el siguiente formato. NO uses comillas dobles (") dentro de los textos.
{json_format}
"""
    user = f"""
ANIME: {clean_title}

HECHOS RECOPILADOS DE MÚLTIPLES FUENTES:
{json.dumps(all_mapped_facts, ensure_ascii=False)}

Genera el Dossier Maestro en JSON:
"""
    return json.dumps([{"role": "system", "content": system}, {"role": "user", "content": user}])


def get_fact_checker_prompt(category: str, clean_title: str, dossier: dict, raw_sources: list) -> str:
    system = """
Eres el Agente de Fact-Checking (Fase 3.5).
Tu trabajo es auditar el Dossier Maestro generado en la fase anterior contra las fuentes crudas.
1. Revisa cada afirmación del Dossier y compárala con las FUENTES CRUDAS proporcionadas.
2. ELIMINA cualquier dato en el Dossier que no esté respaldado directamente por las FUENTES CRUDAS. QUEDA ESTRICTAMENTE PROHIBIDO usar tu propio conocimiento experto para rellenar vacíos. 
3. CRÍTICO: Si determinas que no existen hechos reales, sustanciales y verificables sobre la franquicia/película en las fuentes proporcionadas, debes omitir todo el formato del dossier y devolver estrictamente este JSON: { "status": "INSUFFICIENT_DATA" }. No inventes ni alucines información falsa bajo ningún concepto.
4. Devuelve ÚNICAMENTE el JSON final, ya sea el Dossier Maestro limpio (sin alucinaciones) o el objeto de datos insuficientes.
"""
    # Create a simplified version of raw sources to save tokens
    simplified_sources = [{"title": s.get("title"), "url": s.get("url")} for s in raw_sources] if isinstance(raw_sources, list) else raw_sources
    
    user = f"""
ANIME: {clean_title}

FUENTES CRUDAS ORIGINALES DE REFERENCIA:
{json.dumps(simplified_sources, ensure_ascii=False)}

DOSSIER MAESTRO A AUDITAR Y LIMPIAR:
{json.dumps(dossier, ensure_ascii=False)}

Devuelve el Dossier en JSON estrictamente verificado y libre de alucinaciones:
"""
    return json.dumps([{"role": "system", "content": system}, {"role": "user", "content": user}])


def get_section_writer_prompt(category: str, section_title: str, dossier: dict, images: list, previous_summary: str, reviewer_feedback: str = "") -> str:
    word_count_guideline = ""
    if category == 'novedades':
        word_count_guideline = "La sección debe tener aproximadamente entre 150 y 250 palabras (el artículo final será de 700-1000 palabras)."
    elif category == 'curiosidades':
        word_count_guideline = "La sección debe tener aproximadamente entre 250 y 350 palabras (el artículo final será de 1300-1500 palabras)."
    else: # analisis
        word_count_guideline = "La sección debe tener aproximadamente entre 350 y 450 palabras (el artículo final será de 1700-2000 palabras)."

    if category == 'novedades':
        source_instruction = "USO DE FUENTES: Usa el Dossier Maestro como tu ÚNICA fuente de información. QUEDA ESTRICTAMENTE PROHIBIDO inventar o deducir información, personajes, tramas, estudios, o fechas que no estén explícitamente en el Dossier. No uses tu 'conocimiento experto'. Si el Dossier tiene pocos datos, escribe una sección más corta, priorizando la veracidad absoluta sobre la longitud."
        deduction_instruction = "PROHIBIDO INTERPRETAR O DEDUCIR: Si el Dossier dice \"se anunció una película\", NO deduzcas que \"la serie dejará de existir\" o que \"reemplaza a la temporada 3\". Reporta SOLO lo que el Dossier dice literalmente. NUNCA presentes conclusiones lógicas como hechos confirmados. Si quieres mencionar una posibilidad, usa SIEMPRE frases como \"podría\", \"aún no se confirma\", \"queda por ver\"."
        write_instruction = f'Escribe el Markdown ÚNICAMENTE para la sección "{section_title}" usando EXCLUSIVAMENTE los datos del Dossier Maestro:'
    else:
        source_instruction = "USO DE FUENTES: Usa el Dossier Maestro como tu fuente principal de información. Si el dossier no tiene suficientes detalles o no explica bien el contexto de una curiosidad/dato, PUEDES usar tu propio conocimiento experto VERÍDICO sobre el anime para enriquecer el artículo. CRÍTICO: Tu conocimiento propio debe ser sobre datos verificables, ampliamente documentados y reales. Prohibido inventar."
        deduction_instruction = "PROHIBIDO ESPECULAR Y MODO CONSERVADOR: Si decides usar tu propio conocimiento experto para añadir detalles (personajes, habilidades, estudios, emisoras), debes estar 100% SEGURO de su veracidad y ortografía oficial. Si no recuerdas con precisión absoluta el apellido de un personaje, su clase de juego exacta, su habilidad oficial o el canal de emisión, usa descripciones genéricas (ej. \"el protagonista\", \"la elfa\", \"la guerrera\", \"canales de televisión\") en lugar de escribir nombres específicos que puedan estar equivocados. Queda terminantemente prohibido inventar o asumir detalles técnicos de producción como flujos híbridos, CGI o tasas de frames si no tienes evidencia histórica directa."
        write_instruction = f'Escribe el Markdown ÚNICAMENTE para la sección "{section_title}" usando los datos del Dossier Maestro y tu conocimiento experto verídico (bajo reglas estrictas de no adivinar):'

    system = f"""
Eres un Redactor Periodístico Experto de KenkoAnime, escribiendo un artículo paso a paso.
Se te ha pedido escribir ÚNICAMENTE la sección actual: "{section_title}".

CRÍTICO: 
1. Devuelve ÚNICAMENTE el texto en Markdown de esta sección en ESPAÑOL. No incluyas el JSON ni bloques de código.
2. {source_instruction}
3. {word_count_guideline}
4. {deduction_instruction}
5. PROHIBIDO RELLENO EDITORIAL VACÍO: NO uses frases genéricas como "representa un punto de inflexión", "abre nuevas puertas", "el futuro nunca fue tan prometedor", "promete ser una experiencia", "sin duda alguna". Cada oración debe aportar un dato concreto o un análisis sustantivo basado en el Dossier.
6. PROHIBIDO QUEJARSE: BAJO NINGUNA CIRCUNSTANCIA debes escribir metatextos disculpándote, mencionando el "Dossier Maestro", la "falta de información", o tus "reglas anti-alucinación". 
7. PROHIBIDO CREAR SUBTÍTULOS INTERNOS: No utilices encabezados de Markdown (ej. H2: ##, H3: ###, H4: ####) dentro del cuerpo de tu texto. Desarrolla la sección de forma fluida usando únicamente párrafos de prosa limpia. La estructura del artículo ya la define el sistema.
8. ESTILO Y CALIDAD: Escribe con un tono entretenido, informativo y periodístico.
9. NO repitas información, datos, años o hechos que ya se cubrieron en las secciones anteriores (lee el texto real ya escrito abajo).
"""
    
    images_instruction = "No hay imágenes para insertar en esta sección."
    if images:
        images_instruction = f"INSERTA ESTA IMAGEN DENTRO DE TU TEXTO (después del primer párrafo de la sección) USANDO MARKDOWN: ![Descripción visual]({images[0]})"

    user = f"""
SECCIÓN A ESCRIBIR AHORA:
## {section_title}

FEEDBACK DEL REVISOR (Si aplica):
{reviewer_feedback}

TEXTO REAL DE SECCIONES YA ESCRITAS (¡No repitas los mismos hechos, datos o frases!):
{previous_summary or "Esta es la primera sección (Introducción), no hay nada escrito aún."}

DOSSIER MAESTRO (Tu única fuente de verdad):
{json.dumps(dossier, indent=2, ensure_ascii=False)}

{images_instruction}

{write_instruction}
"""
    return json.dumps([{"role": "system", "content": system}, {"role": "user", "content": user}])


def get_translator_prompt(spanish_markdown: str) -> str:
    system = """
Eres un Traductor Otaku Experto bilingüe (Español a Inglés).
Tu única tarea es tomar un artículo escrito en formato Markdown en español y traducirlo perfectamente al Inglés.

CRÍTICO:
1. DEBES mantener la estructura Markdown exacta (los mismos H1, H2, listas).
2. NO ALTERES los bloques de imágenes `![alt](url)`. Déjalos exactamente como están, solo traduce el texto "alt" si quieres, pero nunca la URL.
3. El tono debe seguir siendo entretenido, informativo y amigable para fans del anime.
4. Devuelve ÚNICAMENTE el Markdown en inglés, sin comentarios adicionales.
"""
    user = f"""
TRADUCE ESTE ARTÍCULO AL INGLÉS MANTENIENDO EL FORMATO MARKDOWN:

{spanish_markdown}
"""
    return json.dumps([{"role": "system", "content": system}, {"role": "user", "content": user}])


def get_reviewer_prompt(category: str, spanish_markdown: str, editor_briefing: dict, dossier: dict, outline: list) -> str:
    system = f"""
Eres el Revisor Final (QA) de KenkoAnime. 
El equipo te ha entregado un borrador de artículo en Español basado en una investigación previa.
Tu trabajo es auditar la veracidad y calidad del texto, y decidir si se aprueba o necesita revisión.
La categoría objetivo de este artículo es: {category.upper()}

CRÍTICO:
1. ANTI-ALUCINACIÓN Y CONTROL DE NOMBRES (FACT-CHECKING DE CONOCIMIENTO GLOBAL): Si el artículo menciona nombres específicos de personajes (ej. apellidos), lore de fantasía (ej. clases de juego, tipos de magia) o detalles técnicos de animación (ej. CGI, paralaje) que NO están respaldados en el DOSSIER MAESTRO, DEBES ser sumamente crítico. Si no tienes certeza absoluta y contrastada de que esos detalles añadidos por el escritor sean 100% verídicos en el canon oficial de la obra, DEBES rechazar el artículo (NEEDS_REVISION) e indicarle al escritor que use términos genéricos (ej. "el protagonista", "la guerrera elfa") o que elimine la afirmación técnica inventada. Es mejor un texto genérico y correcto que uno específico y falso.
2. DETECCIÓN DE INTERPRETACIONES: Si el artículo presenta conclusiones o deducciones como hechos confirmados (ej. "la serie dejará de continuar en formato de serie", "esta será la continuación canónica definitiva") pero el Dossier NO dice eso explícitamente, DEBES rechazarlo (NEEDS_REVISION). El artículo debe reportar hechos, no interpretar.
3. DETECCIÓN DE RELLENO VACÍO: Si el artículo usa frases genéricas de relleno que no aportan información (ej. "representa un punto de inflexión", "abre nuevas puertas", "el futuro nunca fue tan prometedor", "promete ser una experiencia inmersiva"), DEBES rechazarlo (NEEDS_REVISION) pidiendo que se sustituyan por datos concretos o se eliminen.
4. AUDITORÍA Y COHERENCIA: Revisa que el artículo tenga coherencia absoluta con la categoría ({category.upper()}) y su formato. Todo lo que se hable debe estar estrictamente relacionado con el objetivo del artículo.
5. DETECCIÓN DE EXCUSAS: Si el artículo contiene menciones meta textuales (ej. "No hay suficiente información", "Según mis reglas", etc.), DEBES rechazarlo (NEEDS_REVISION).
6. Devuelve ESTRICTAMENTE un objeto JSON con este formato crudo:
{{
  "status": "APPROVED" | "NEEDS_REVISION",
  "feedback": "Si es APPROVED, déjalo vacío. Si es NEEDS_REVISION, escribe instrucciones claras al redactor sobre qué arreglar.",
  "sections_to_fix": [1, 3] // Si es NEEDS_REVISION, devuelve un array con los NÚMEROS (1-indexados) de las secciones que tienen problemas y deben reescribirse. Si todo el artículo está mal, pon todas.
}}
"""
    outline_str = "\n".join([f"{i+1}. {title}" for i, title in enumerate(outline)])
    
    user = f"""
TÍTULO BASE DEL ANIME: {editor_briefing.get("cleanTitle")}

--- ESQUELETO DEL ARTÍCULO ---
{outline_str}

--- DOSSIER MAESTRO (Tu única fuente de verdad) ---
{json.dumps(dossier, indent=2, ensure_ascii=False)}

--- BORRADOR EN ESPAÑOL A REVISAR ---
{spanish_markdown}

Devuelve el veredicto en JSON crudo:
"""
    return json.dumps([{"role": "system", "content": system}, {"role": "user", "content": user}])

def get_titulator_prompt(spanish_markdown: str, english_markdown: str, editor_briefing: dict) -> str:
    system = """
Eres el Agente Titulador de KenkoAnime. 
Tu trabajo es empaquetar la metadata de un artículo bilingüe generado en el formato JSON estricto requerido por la base de datos.
CRÍTICO:
1. El JSON debe ser perfecto y crudo. NO añadas ningún saludo, explicación, ni bloques de código (```json). SOLO el objeto.

Formato requerido:
{
  "title_es": "Título atractivo y creativo en español",
  "title_en": "Catchy creative title in English",
  "excerpt_es": "Breve resumen de 2 líneas del artículo en español",
  "excerpt_en": "Short 2-line summary of the article in English",
  "imageAlt": "Descripción descriptiva de la imagen principal para accesibilidad",
  "tags": ["tag1", "tag2", "tag3"]
}
"""
    user = f"""
TÍTULO BASE DEL ANIME: {editor_briefing.get("cleanTitle")}

--- VERSIÓN EN ESPAÑOL ---
{spanish_markdown}

--- VERSIÓN EN INGLÉS ---
{english_markdown}

Extrae títulos llamativos, genera los resúmenes (excerpts), y devuelve el JSON crudo perfecto:
"""
    return json.dumps([{"role": "system", "content": system}, {"role": "user", "content": user}])

def get_image_agent_prompt(anime_title: str, image_urls: list) -> str:
    system = """
Eres el Agente de Auditoría Visual (QA de Imágenes) de KenkoAnime.
Tu trabajo es analizar una lista de URLs de imágenes usadas en un artículo sobre un anime específico.
Debes determinar si cada URL (por su dominio, ruta o palabras clave en el enlace) parece tener relación con el anime o si es una imagen genérica irrelevante (como fotos de unsplash).

Devuelve ESTRICTAMENTE un JSON crudo con el siguiente formato:
{
  "url_analysis": [
    {
      "url": "la_url_evaluada",
      "status": "KEEP" | "REPLACE",
      "reason": "Breve explicación"
    }
  ]
}
"""
    user = f"""
ANIME: {anime_title}

URLS A EVALUAR:
{json.dumps(image_urls, indent=2)}

Devuelve el análisis en JSON crudo:
"""
    return json.dumps([{"role": "system", "content": system}, {"role": "user", "content": user}])

def get_corrector_prompt(spanish_markdown: str, feedback: str, dossier: dict) -> str:
    system = """
Eres el Agente Corrector de KenkoAnime. Tu tarea es recibir un borrador de artículo en Markdown y el feedback crítico del Revisor, y generar una versión corregida del artículo completo.

CRÍTICO:
1. Devuelve ÚNICAMENTE el texto en Markdown corregido. No incluyas explicaciones, saludos ni confirmaciones.
2. Aplica exactamente los cambios solicitados en el FEEDBACK DEL REVISOR.
3. Mantén intacta la estructura general, las imágenes y el contenido que ya estaba correcto.
4. Tu fuente de la verdad absoluta para cualquier corrección de datos es el DOSSIER MAESTRO.
"""
    user = f"""
--- DOSSIER MAESTRO ---
{json.dumps(dossier, indent=2, ensure_ascii=False)}

--- BORRADOR ACTUAL ---
{spanish_markdown}

--- FEEDBACK DEL REVISOR ---
{feedback}

Por favor, reescribe y corrige el BORRADOR ACTUAL aplicando el FEEDBACK. Devuelve SOLO el Markdown final corregido:
"""
    return json.dumps([{"role": "system", "content": system}, {"role": "user", "content": user}])
