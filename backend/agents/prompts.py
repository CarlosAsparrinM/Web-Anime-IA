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
  "topicFocus": "Breve instrucción de 1 párrafo para el escritor sobre qué enfoque darle al artículo basado en la sinopsis y categoría",
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
Calificación: {data.get("score", "N/A")}/10
{images_context}

Genera el JSON del Briefing:
"""
    return json.dumps([{"role": "system", "content": system}, {"role": "user", "content": user}])


def get_researcher_prompt(category: str, clean_title: str, tavily_data: str) -> str:
    today_date = datetime.now().strftime("%Y-%m-%d")
    
    if category == 'novedades':
        json_format = """{
  "newsEvent": "Qué pasó exactamente (el evento o anuncio)",
  "context": "Breve contexto del anime para quien no lo conoce",
  "keyFacts": ["Dato clave 1", "Dato clave 2"]
}"""
        extra_instruction = f"HOY ES {today_date}. Esta es una noticia de ÚLTIMA HORA. Ignora información de años pasados y céntrate en los anuncios recientes."
    elif category == 'curiosidades':
        json_format = """{
  "triviaList": [
    "Dato curioso o easter egg 1",
    "Dato curioso o easter egg 2",
    "Dato curioso o easter egg 3",
    "Dato curioso o easter egg 4",
    "Dato curioso o easter egg 5"
  ]
}"""
        extra_instruction = "Busca secretos de producción, datos del mangaka, curiosidades del lore, etc."
    else: # analisis
        json_format = """{
  "studio": "Estudio de animación (si se menciona, sino 'Desconocido')",
  "characters": ["Nombre 1 - Breve rol", "Nombre 2 - Breve rol"],
  "realSynopsis": "Resumen detallado de la trama real según internet",
  "keyFacts": ["Dato interesante de animación", "Dato interesante de recepción"]
}"""
        extra_instruction = "Extrae datos precisos sobre la trama general, los personajes y el recibimiento crítico."

    system = f"""
Eres el Investigador Experto de KenkoAnime. Tu trabajo es leer información cruda extraída de internet (mediante web scraping) y convertirla en un "Dossier de Datos Duros" altamente preciso.
Debes extraer la verdad absoluta para evitar que el Escritor invente datos (alucinaciones).

{extra_instruction}

CRÍTICO:
Debes devolver ESTRICTAMENTE un objeto JSON con el siguiente formato. 
IMPORTANTE: NUNCA uses comillas dobles (") dentro de los textos, usa comillas simples (') para evitar romper el formato JSON.
{json_format}
"""
    user = f"""
TÍTULO DEL ANIME: {clean_title}

DATOS EXTRAÍDOS DE INTERNET (Tavily):
{tavily_data}

Genera el JSON del Dossier (Solo responde con el objeto JSON válido):
"""
    return json.dumps([{"role": "system", "content": system}, {"role": "user", "content": user}])


def get_writer_prompt(category: str, editor_briefing: dict, raw_data: dict, research_dossier: dict) -> str:
    if category == 'novedades':
        estructura = """ESTRUCTURA OBLIGATORIA (Mínimo 500 palabras):
- H1: [Titular de la Noticia]
- Introducción: Directo al grano (Qué pasó). 2 párrafos.
- [Inserta una imagen aquí si hay]
- H2: El Anuncio / La Novedad: Desarrollo profundo de la noticia. Mínimo 3 párrafos.
- H2: Contexto: Análisis detallado de qué trata este anime para quien no lo conoce. Mínimo 2 párrafos.
- [Inserta otra imagen aquí si hay]"""
    elif category == 'curiosidades':
        estructura = """ESTRUCTURA OBLIGATORIA (Mínimo 800 palabras):
- H1: [Número] Cosas que no sabías de [Anime]
- Introducción: Gancho emocional extenso para los fans.
- [Inserta una imagen aquí si hay]
- H2: [Título de Curiosidad 1] (Mínimo 2 párrafos largos)
- H2: [Título de Curiosidad 2] (Mínimo 2 párrafos largos)
- [Inserta otra imagen aquí si hay]
- H2: [Título de Curiosidad 3] (Mínimo 2 párrafos largos)
- H2: [Título de Curiosidad 4] (Mínimo 2 párrafos largos)
- H2: [Título de Curiosidad 5] (Mínimo 2 párrafos largos)"""
    else: # analisis
        estructura = """ESTRUCTURA OBLIGATORIA (Mínimo 1000 palabras):
- H1: Análisis Profundo / Por qué ver [Anime]
- Introducción: Gancho emocional y sinopsis expansiva.
- [Inserta una imagen aquí si hay]
- H2: ¿De qué trata? (La Historia sin Spoilers detallada, mínimo 3 párrafos)
- H2: Personajes Clave (Análisis profundo de motivaciones, mínimo 3 párrafos)
- [Inserta otra imagen aquí si hay]
- H2: Animación y Aspectos Técnicos (Mínimo 2 párrafos)
- H2: Veredicto Final / ¿Para quién es? (Mínimo 2 párrafos)"""

    system = f"""
Eres un Redactor Experto (Writer) de KenkoAnime, un blog premium de anime. Tu estilo es informativo, entretenido y otaku.
Vas a recibir un "Briefing" del Editor, datos crudos de la API, y un "Dossier" verídico del Investigador.

CRÍTICO: 
1. Tu respuesta DEBE ser ÚNICAMENTE el artículo redactado en formato Markdown en ESPAÑOL. NO devuelvas JSON. No uses inglés.
2. NO INVENTES NADA. Usa estrictamente los datos proporcionados en el Dossier de Investigación y los Datos Crudos.
3. Debes insertar las imágenes seleccionadas por el editor DENTRO de tu Markdown usando ![Descripción](URL) justo después de los subtítulos.
4. REGLA DE EXTENSIÓN ESTRICTA: Escribe TODO el contenido en Español. Eres un experto en SEO y redacción persuasiva. Los artículos deben ser MUY LARGOS Y DETALLADOS. Debes profundizar excesivamente en cada sección. Cada H2 debe contener obligatoriamente entre 2 y 4 párrafos extensos (al menos 80 palabras por párrafo). ¡NO SEAS BREVE! Tómate tu tiempo para describir las emociones, el contexto y la importancia de la información. Exprime tu creatividad al máximo.

{estructura}
"""
    
    selected_images = editor_briefing.get("selectedImages", [])
    images_instruction = "No hay imágenes extra para insertar en el cuerpo del artículo."
    if selected_images:
        images_instruction = f"Imágenes a usar (NO LAS REPITAS, ÚSALAS TODAS 1 VEZ): {', '.join(selected_images)}\nRecuerda colocar las imágenes después de los subtítulos."

    user = f"""
DATOS CRUDOS (API):
Géneros: {", ".join(raw_data.get("genres", [])) or "Varios"}
Año: {raw_data.get("year", "N/A")}
Calificación: {raw_data.get("score", "N/A")}/10

BRIEFING DEL EDITOR:
Anime: {editor_briefing.get("cleanTitle")}
Enfoque Solicitado: {editor_briefing.get("topicFocus")}
{images_instruction}

DOSSIER DE INVESTIGACIÓN (¡Usa estos datos reales!):
{json.dumps(research_dossier, indent=2, ensure_ascii=False)}

¡Escribe solo el Markdown en Español siguiendo la ESTRUCTURA OBLIGATORIA para la categoría {category.upper()}, asegurándote de que sea un artículo muy largo y detallado!
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
3. El JSON debe ser perfecto y crudo (sin bloques de código ```json).

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
