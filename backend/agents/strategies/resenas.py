from .base import BaseStrategy
from agents.sources import fetch_anime_for_review

class ResenasStrategy(BaseStrategy):
    REDUCE_JSON_FORMAT = """{
  "officialSynopsis": "Resumen fiel de la trama de esta temporada/película",
  "production": { "studio": "", "director": "", "writer": "", "composer": "", "year": "" },
  "themes": ["Tema 1", "Tema 2"],
  "characters": [{ "name": "", "role": "", "traits": "" }],
  "worldBuilding": ["Detalle 1", "Detalle 2"],
  "criticalReception": ["Recepción 1", "Recepción 2"],
  "pros": ["Punto a favor 1"],
  "cons": ["Punto en contra 1"]
}"""
    
    REDUCE_EXTRA_INSTRUCTION = "Construye un dossier para hacer una RESEÑA CRÍTICA de esta entrega específica (temporada, película u OVA). Extrae los puntos fuertes (pros) y puntos débiles (cons) mencionados por la crítica o el público. Conserva detalles de producción precisos."
    
    WRITER_WORD_COUNT_GUIDELINE = "La sección debe tener la longitud dictada por tu meta de palabras (el artículo final será de 800-1000 palabras)."
    TARGET_WORD_COUNT = 900
    
    WRITER_SOURCE_INSTRUCTION = "USO DE FUENTES: Usa el Dossier Maestro como tu fuente principal de información. Si el dossier no tiene suficientes detalles, PUEDES usar tu propio conocimiento experto VERÍDICO sobre el anime para enriquecer el artículo. Al ser una reseña, puedes adoptar un tono ligeramente valorativo basándote en la 'Recepción Crítica', 'Pros' y 'Cons' del dossier, pero mantén la objetividad periodística. Los datos duros del anime (número de episodios, géneros, estudios, año) son INMUTABLES."
    
    WRITER_DEDUCTION_INSTRUCTION = "PROHIBIDO ESPECULAR: Si decides usar tu propio conocimiento experto para añadir detalles (personajes, habilidades, estudios), debes estar 100% SEGURO de su veracidad. No inventes críticas negativas o positivas que no apliquen a la obra."
    
    MAP_BLACKLIST_INSTRUCTION = """CRÍTICO - LISTA NEGRA: Descarta INMEDIATAMENTE cualquier dato que:
- Provenga de Instagram, TikTok, Reddit, Twitter, YouTube.
- Mencione seguidores, likes, views, posts, stories, hashtags.
- Mencione cosplay, fanarts o merchandising.
NOTA: SÍ debes extraer reseñas críticas, opiniones fundamentadas de sitios especializados, y detalles técnicos."""

    async def fetch_data(self) -> dict:
        for attempt in range(5):
            try:
                source_data = await fetch_anime_for_review()
                print(f"--> Selected valid anime for reseña: {source_data.get('title')}")
                return source_data
            except Exception as e:
                print(f"--> Failed attempt {attempt+1} fetching review anime: {e}")
                
        raise Exception("Failed to fetch valid data for resenas")

    def get_tavily_query(self, clean_title: str, source_data: dict) -> str:
        return f'{clean_title} anime review critique analysis pros cons'

    def check_dossier_quality(self, dossier: dict) -> bool:
        has_synopsis = bool(dossier.get("officialSynopsis"))
        reception = dossier.get("criticalReception", [])
        has_reception = isinstance(reception, list) and len(reception) >= 1
        
        if not has_synopsis:
            print("--> Quality Gate FAILED: No officialSynopsis found in dossier.")
            return False
        if not has_reception:
            print("--> Quality Gate FAILED: No criticalReception found in dossier.")
            return False
            
        print(f"--> Quality Gate PASSED: synopsis=OK, criticalReception={len(reception)}")
        return True

    def get_outline(self, dossier: dict, title: str) -> list:
        return [f"Introducción a {title}", "Trama y Desarrollo", "Animación y Banda Sonora", "Veredicto y Calificación"]
