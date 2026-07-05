import json
from datetime import datetime

def get_editor_prompt(category: str, data: dict) -> str:
    images_context = "Imágenes disponibles: Ninguna"
    if data.get("extraImages"):
        images_context = "Imágenes disponibles:\n" + "\n".join([f"- {img}" for img in data["extraImages"]])

    system = """
Eres el Editor en Jefe de KenkoAnime. Tu trabajo es recibir datos crudos de una API de anime y "limpiarlos" para el equipo de redacción.
El nombre que viene de la API a veces tiene subtítulos molestos (ej. "Part 3", "OVA", "Chapter 4"). Si es un artículo general, debes extraer el nombre de la franquicia.
Debes devolver ESTRICTAMENTE un objeto JSON con el siguiente formato:
{
  "cleanTitle": "Nombre limpio de la franquicia o título con sentido",
  "topicFocus": "Instrucción estricta para el escritor sobre qué enfoque darle (ej. Si la categoría es CURIOSIDADES, ordénale centrarse SOLO en listar secretos y easter eggs).",
  "selectedImages": ["url1", "url2", "url3"] // Selecciona hasta 3 o 4 imágenes, si hay disponibles, que tengan sentido
}
"""
    user = f"""
CATEGORÍA DEL ARTÍCULO: {category.upper()}
DATOS CRUDOS:
Título Original: {data.get("title")}
Sinopsis: {data.get("synopsis")}
Año: {data.get("year", "N/A")}
Géneros: {", ".join(data.get("genres", [])) or "Varios"}
Calificación (MyAnimeList): {data.get("score", "N/A")}/10
{images_context}

Genera el JSON del Briefing:
"""
    return json.dumps([{"role": "system", "content": system}, {"role": "user", "content": user}])


def get_researcher_map_prompt(category: str, clean_title: str, single_source: dict) -> str:
    system = """
Eres un Asistente de Investigación (Fase MAP).
Tu trabajo es leer el texto extraído de una ÚNICA página web y extraer SÓLO los hechos verificables, datos y citas útiles sobre el anime indicado, ignorando la basura de la web.
Devuelve ESTRICTAMENTE un objeto JSON con este formato:
{
  "facts": ["Hecho 1", "Hecho 2", ...]
}
"""
    user = f"""
CATEGORÍA: {category.upper()}
ANIME: {clean_title}

FUENTE: {single_source.get('title')}
CONTENIDO:
{str(single_source.get('raw_content') or single_source.get('content'))[:3500]}

Extrae los hechos relevantes para el anime y categoría en el JSON solicitado:
"""
    return json.dumps([{"role": "system", "content": system}, {"role": "user", "content": user}])


def get_researcher_reduce_prompt(category: str, clean_title: str, all_mapped_facts: list) -> str:
    today_date = datetime.now().strftime("%Y-%m-%d")
    
    if category == 'novedades':
        json_format = """{
  "newsEvent": "Qué pasó exactamente (el evento o anuncio)",
  "context": "Breve contexto del anime para quien no lo conoce",
  "keyFacts": ["Dato clave 1", "Dato clave 2"]
}"""
        extra_instruction = f"HOY ES {today_date}. Esta es una noticia de ÚLTIMA HORA. Extrae la verdad de los fragmentos."
    elif category == 'curiosidades':
        json_format = """{
  "triviaList": [
    "Dato curioso detallado 1",
    "Dato curioso detallado 2",
    "..."
  ]
}"""
        extra_instruction = "Consolida los hechos en una lista rica de curiosidades y secretos de producción sin repetirse."
    else: # analisis
        json_format = """{
  "studio": "Estudio de animación (o Desconocido)",
  "characters": ["Nombre 1 - Breve rol", "Nombre 2 - Breve rol"],
  "realSynopsis": "Resumen detallado de la trama real",
  "keyFacts": ["Dato interesante de animación", "Dato interesante de recepción"]
}"""
        extra_instruction = "Consolida los hechos precisos sobre la trama general, los personajes y el recibimiento crítico."

    system = f"""
Eres el Investigador Principal (Fase REDUCE).
Has recibido una lista de hechos extraídos de múltiples fuentes web sobre el anime.
Tu trabajo es consolidarlos, eliminar duplicados y devolver un "Dossier Maestro" estructurado.
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


def get_section_writer_prompt(category: str, section_title: str, dossier: dict, images: list, previous_summary: str) -> str:
    system = f"""
Eres un Redactor Experto de KenkoAnime, escribiendo un artículo paso a paso.
Se te ha pedido escribir ÚNICAMENTE la sección actual: "{section_title}".

CRÍTICO: 
1. Devuelve ÚNICAMENTE el texto en Markdown de esta sección en ESPAÑOL. No incluyas el JSON ni bloques de código.
2. NO INVENTES NADA. Usa estrictamente los datos proporcionados en el Dossier Maestro.
3. Debes desarrollar esta sección ampliamente (al menos 80-100 palabras por párrafo). ¡NO SEAS BREVE! Profundiza en lore, personalidad, impacto emocional, o los detalles del anuncio.
4. REGLA ANTI-ALUCINACIÓN (CERO INVENTOS): NO inventes nombres de canciones (openings/endings), directores, estudios, actores de voz o formatos. Si el Dossier no lo menciona explícitamente, NO LO PONGAS.
5. NO repitas información que ya se cubrió en las secciones anteriores (lee el resumen de lo ya escrito).
"""
    
    images_instruction = "No hay imágenes para insertar en esta sección."
    if images:
        images_instruction = f"INSERTA ESTA IMAGEN DENTRO DE TU TEXTO (después del primer párrafo de la sección) USANDO MARKDOWN: ![Descripción visual]({images[0]})"

    user = f"""
SECCIÓN A ESCRIBIR AHORA:
## {section_title}

RESUMEN DE SECCIONES YA ESCRITAS (¡No repitas esta información!):
{previous_summary or "Esta es la primera sección (Introducción), no hay nada escrito aún."}

DOSSIER MAESTRO (Tu única fuente de verdad):
{json.dumps(dossier, indent=2, ensure_ascii=False)}

{images_instruction}

Escribe el Markdown ÚNICAMENTE para la sección "{section_title}" con muchísima profundidad y análisis, respetando las reglas anti-alucinación:
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


def get_reviewer_prompt(spanish_markdown: str, english_markdown: str, editor_briefing: dict) -> str:
    system = """
Eres el Revisor Final (QA) de KenkoAnime. 
El equipo te ha entregado dos versiones del mismo artículo (una en Español y otra en Inglés).
Tu trabajo es empaquetar esto en el formato JSON estricto requerido por la base de datos.

CRÍTICO:
1. DEBES escapar TODOS los saltos de línea dentro de las cadenas de texto Markdown usando \\n. NO uses saltos de línea literales (Enters).
2. Verifica que las comillas dobles dentro del markdown estén escapadas si es necesario.
3. CONTROL DE VERACIDAD (FACT-CHECKING): Si notas que las versiones generadas mencionan nombres de canciones, bandas, o directores muy específicos que parecen alucinaciones obvias o fuera de lugar, suavízalo o recorta esas partes al empaquetar el contenido final.
4. El JSON debe ser perfecto y crudo (sin bloques de código ```json).

Formato requerido:
{
  "title_es": "Título atractivo y creativo en español",
  "title_en": "Catchy creative title in English",
  "excerpt_es": "Breve resumen de 2 líneas del artículo en español",
  "excerpt_en": "Short 2-line summary of the article in English",
  "content_es": "Contenido Markdown en Español (escapado)\\n\\n...",
  "content_en": "Contenido Markdown en Inglés (escapado)\\n\\n...",
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

Por favor, extrae títulos llamativos de los H1, genera los resúmenes (excerpts) y devuelve el JSON crudo perfecto:
"""
    return json.dumps([{"role": "system", "content": system}, {"role": "user", "content": user}])
