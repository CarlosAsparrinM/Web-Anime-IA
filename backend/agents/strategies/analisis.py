from .base import BaseStrategy
from agents.sources import fetch_classic_anime

class AnalisisStrategy(BaseStrategy):
    REDUCE_JSON_FORMAT = """{
  "officialSynopsis": "Resumen fiel de la trama",
  "production": { "studio": "", "director": "", "writer": "", "composer": "", "year": "" },
  "themes": ["Tema 1", "Tema 2", "Tema 3"],
  "characters": [{ "name": "", "role": "", "traits": "" }],
  "worldBuilding": ["Detalle 1", "Detalle 2"],
  "lore": ["Secreto 1", "Mito 2"],
  "criticalReception": ["Recepción 1"],
  "interestingFacts": ["Producción secreta"]
}"""
    
    REDUCE_EXTRA_INSTRUCTION = "Construye un dossier enciclopédico sumamente rico, denso y profundo SOBRE TODA LA FRANQUICIA O LA OBRA COMPLETA (es un clásico o anime finalizado). Agrupa todos los personajes con sus nombres y apellidos correctos, roles y habilidades que vengan en las fuentes. Conserva detalles de producción muy precisos. Evita resúmenes genéricos y enfócate en el impacto, temas profundos y legado."
    
    WRITER_WORD_COUNT_GUIDELINE = "La sección debe tener aproximadamente entre 260 y 300 palabras (el artículo final será de 1300-1500 palabras)."
    TARGET_WORD_COUNT = 1400
    
    WRITER_SOURCE_INSTRUCTION = "USO DE FUENTES: Usa el Dossier Maestro como tu fuente principal de información. Si el dossier no tiene suficientes detalles o no explica bien el contexto de una curiosidad/dato, PUEDES usar tu propio conocimiento experto VERÍDICO sobre el anime para enriquecer el artículo. CRÍTICO: Tu conocimiento propio debe ser sobre datos verificables, ampliamente documentados y reales. Prohibido inventar.\\nSi describes un personaje, usa EXCLUSIVAMENTE la descripción que aparece en el Dossier. No inventes roles, profesiones, relaciones ni habilidades que no estén explícitamente escritas en el Dossier.\\nLos datos duros del anime (número de episodios, géneros, estudios, año) son INMUTABLES. Cópialos textualmente del Dossier sin modificar, redondear ni ambiguar.\\nPROHIBIDO presentar opiniones, comparaciones con otros directores/obras, o interpretaciones subjetivas como hechos. Si haces una comparación estilística, usa siempre frases como 'ha sido comparado por algunos con...' o 'recuerda al estilo de...'."
    
    WRITER_DEDUCTION_INSTRUCTION = "PROHIBIDO ESPECULAR Y MODO CONSERVADOR: Si decides usar tu propio conocimiento experto para añadir detalles (personajes, habilidades, estudios, emisoras), debes estar 100% SEGURO de su veracidad y ortografía oficial. Si no recuerdas con precisión absoluta el apellido de un personaje, su clase de juego exacta, su habilidad oficial o el canal de emisión, usa descripciones genéricas (ej. \"el protagonista\", \"la elfa\", \"la guerrera\", \"canales de televisión\") en lugar de escribir nombres específicos que puedan estar equivocados. Queda terminantemente prohibido inventar o asumir detalles técnicos de producción como flujos híbridos, CGI o tasas de frames si no tienes evidencia histórica directa.\\nSi el Dossier dice que un personaje es 'una enfermera', NO escribas que es 'un capoeirista'. Si no estás 100% seguro del ROL EXACTO de un personaje en la serie, descríbelo de forma genérica (ej. 'uno de los personajes secundarios') en lugar de asignarle un rol inventado."
    
    MAP_BLACKLIST_INSTRUCTION = """CRÍTICO - LISTA NEGRA: Descarta INMEDIATAMENTE cualquier dato que:
- Provenga de Instagram, TikTok, Reddit, Twitter, YouTube.
- Mencione seguidores, likes, views, posts, stories, hashtags.
- Mencione cosplay, fanarts o merchandising de nicho sin valor informativo.
NOTA: Para análisis y curiosidades, SÍ debes extraer análisis temáticos de la trama, conceptos filosóficos de la obra, recepción crítica, detalles de producción, impacto cultural e interpretaciones oficiales ampliamente aceptadas."""

    async def fetch_data(self) -> dict:
        for attempt in range(5):
            try:
                source_data = await fetch_classic_anime()
                print(f"--> Selected valid anime for analisis: {source_data.get('title')}")
                return source_data
            except Exception as e:
                print(f"--> Failed attempt {attempt+1} fetching classic anime: {e}")
                
        raise Exception("Failed to fetch valid data for analisis")

    def get_tavily_query(self, clean_title: str, source_data: dict) -> str:
        return f'{clean_title} anime plot characters animation review'

    def check_dossier_quality(self, dossier: dict) -> bool:
        has_synopsis = bool(dossier.get("officialSynopsis"))
        characters = dossier.get("characters", [])
        has_characters = isinstance(characters, list) and len(characters) >= 2
        themes = dossier.get("themes", [])
        has_themes = isinstance(themes, list) and len(themes) >= 1
        
        if not has_synopsis:
            print("--> Quality Gate FAILED: No officialSynopsis found in dossier.")
            return False
        if not has_characters:
            print(f"--> Quality Gate FAILED: Only {len(characters) if isinstance(characters, list) else 0} characters found (min 2 required).")
            return False
        if not has_themes:
            print("--> Quality Gate FAILED: No themes found in dossier.")
            return False
        print(f"--> Quality Gate PASSED: synopsis=OK, characters={len(characters)}, themes={len(themes)}")
        return True

    def get_outline(self, dossier: dict, title: str) -> list:
        return [f"Introducción al Legado de {title}", "Temas Profundos y Filosofía", "Desarrollo de Personajes", "Producción y Arte Visual", "Impacto Cultural y Conclusión"]
