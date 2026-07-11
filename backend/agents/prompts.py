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


def get_researcher_map_prompt(category: str, clean_title: str, single_source: dict, blacklist_instruction: str) -> str:

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


def get_researcher_reduce_prompt(category: str, clean_title: str, all_mapped_facts: list, api_data: dict, json_format: str, extra_instruction: str) -> str:

    confidence_rule = 'Acepta hechos que vengan marcados con confidence: "HIGH" o "MEDIUM". Descarta los LOW (que son solo ruido de la web o comentarios irrelevantes).'

    system = f"""
Eres el Investigador Principal (Fase REDUCE).
Has recibido una lista de hechos extraídos de múltiples fuentes web sobre el anime.
Tu trabajo es consolidarlos, eliminar duplicados y devolver un "Dossier Maestro" estructurado.

DATOS INMUTABLES DE LA API (NO MODIFICAR):
- Episodios: {api_data.get('episodes')}
- Géneros: {', '.join(api_data.get('genres', []))}
- Estudios: {', '.join(api_data.get('studios', []))}
- Año: {api_data.get('year')}
- Calificación: {api_data.get('score')}
Estos datos provienen directamente de MyAnimeList/Jikan y son la VERDAD ABSOLUTA. Inclúyelos textualmente en el Dossier sin modificar.

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
4. VERIFICACIÓN DE PERFILES: Si el Dossier asigna roles, profesiones o descripciones específicas a personajes, verifica que esas descripciones estén respaldadas por al menos una fuente cruda. Si un personaje es descrito con un rol que no aparece en ninguna fuente, ELIMINA esa descripción del Dossier.
5. Devuelve ÚNICAMENTE el JSON final, ya sea el Dossier Maestro limpio (sin alucinaciones) o el objeto de datos insuficientes.
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


def get_section_writer_prompt(category: str, section_title: str, dossier: dict, images: list, previous_summary: str, word_count_guideline: str, source_instruction: str, deduction_instruction: str, reviewer_feedback: str = "", target_words: int = 0) -> str:
    if target_words > 0:
        word_count_guideline = f"META DE PALABRAS: Escribe esta sección utilizando aproximadamente {target_words} palabras. Ajusta tu nivel de detalle para cumplir esta meta sin usar frases de relleno ni dar rodeos vacíos."
    write_instruction = f'Escribe el Markdown ÚNICAMENTE para la sección "{section_title}" usando EXCLUSIVAMENTE los datos del Dossier Maestro:' if category == 'novedades' else f'Escribe el Markdown ÚNICAMENTE para la sección "{section_title}" usando los datos del Dossier Maestro y tu conocimiento experto verídico (bajo reglas estrictas de no adivinar):'

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
9. PROHIBIDO REPETIR CONCEPTOS: No repitas ideas que ya fueron cubiertas en secciones anteriores. Si la introducción ya mencionó que los personajes están interconectados, no lo repitas en la sección de personajes. Cada sección debe aportar información NUEVA (lee el texto real ya escrito abajo).
10. PROHIBIDO JERGA DE IA: No uses terminología técnica que suene artificial como 'bucle recursivo', 'planificación digital integrada', 'motor narrativo'. Escribe con un lenguaje periodístico natural y accesible.
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
2. VERIFICACIÓN DE PERSONAJES: Si el artículo asigna un ROL ESPECÍFICO a un personaje (ej. 'estudiante', 'influencer', 'capoeirista'), VERIFICA que ese rol aparezca literalmente en el Dossier Maestro. Si el Dossier dice algo distinto o no menciona ese rol, RECHAZA el artículo (NEEDS_REVISION) indicando exactamente qué personaje tiene un rol incorrecto.
3. DETECCIÓN DE OPINIONES COMO HECHOS Y EXAGERACIONES: Si el artículo presenta comparaciones estilísticas (ej. 'como el cine de Tarantino') o juicios de valor como si fueran datos objetivos, o eleva un elemento parcial a 'eje absoluto' o 'centro de toda la historia' sin respaldo, RECHAZA el artículo (NEEDS_REVISION).
4. DETECCIÓN DE RELLENO VACÍO Y REDUNDANCIA: Si el artículo usa frases genéricas de relleno, o si repite la misma idea o concepto en múltiples secciones (ej. 'los personajes están interconectados' aparece 3 veces), RECHAZA el artículo (NEEDS_REVISION) indicando las repeticiones.
5. VERIFICACIÓN DE DATOS DUROS: Compara el número de episodios, géneros y estudios mencionados en el artículo contra los del Dossier. Si hay discrepancias (ej. '12-13 episodios' cuando el Dossier dice '13'), RECHAZA el artículo (NEEDS_REVISION).
6. AUDITORÍA Y COHERENCIA: Revisa que el artículo tenga coherencia absoluta con la categoría ({category.upper()}) y su formato. Todo lo que se hable debe estar estrictamente relacionado con el objetivo del artículo.
7. DETECCIÓN DE EXCUSAS: Si el artículo contiene menciones meta textuales (ej. "No hay suficiente información", "Según mis reglas", etc.), DEBES rechazarlo (NEEDS_REVISION).
8. Devuelve ESTRICTAMENTE un objeto JSON con este formato crudo:
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

def get_architect_prompt(category: str, clean_title: str, dossier: dict, outline: list, total_target_words: int) -> str:
    system = f"""
Eres el Agente Arquitecto de KenkoAnime. Tu trabajo es leer el Dossier Maestro y planificar la distribución de palabras para cada sección del artículo.
Se te ha dado un límite total de {total_target_words} palabras.
Debes analizar la densidad, complejidad y cantidad de información disponible en el Dossier para cada tema, y asignar una meta de palabras (`word_target`) a cada sección del esqueleto proporcionado.
Las secciones con mucha información deben recibir más palabras, y las que tienen poca información (o son introducciones/conclusiones) deben recibir menos palabras.
La suma de todos los `word_target` debe ser aproximadamente {total_target_words}.

Devuelve ESTRICTAMENTE un arreglo JSON con el siguiente formato, respetando los títulos de sección originales:
[
  {{ "title": "Introducción", "word_target": 150 }},
  {{ "title": "Curiosidad #1: X", "word_target": 350 }}
]
"""
    user = f"""
ANIME: {clean_title}
META TOTAL DE PALABRAS: {total_target_words}

--- ESQUELETO DEL ARTÍCULO (Asigna palabras a cada uno de estos títulos exactos) ---
{json.dumps(outline, ensure_ascii=False)}

--- DOSSIER MAESTRO ---
{json.dumps(dossier, ensure_ascii=False)}

Genera la estructura JSON con las metas de palabras asignadas:
"""
    return json.dumps([{"role": "system", "content": system}, {"role": "user", "content": user}])
