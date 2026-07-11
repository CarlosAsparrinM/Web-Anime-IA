from .base import BaseStrategy
from agents.sources import fetch_random_anime

class CuriosidadesStrategy(BaseStrategy):
    REDUCE_JSON_FORMAT = """{
  "triviaList": [
    {
      "fact": "Curiosidad única y específica (ej. censura, referencias, cambios)",
      "context": "Contexto detallado de la curiosidad",
      "source": "Fuente original"
    }
  ]
}"""
    
    REDUCE_EXTRA_INSTRUCTION = "AGRUPA Y FILTRA: No repitas el mismo dato de producción varias veces. Busca curiosidades DIVERSAS: cambios entre manga y anime, inspiraciones del autor, censura, referencias, cameos, récords. Si solo hay 3 curiosidades DIVERSAS reales en las fuentes, devuelve solo 3, no inventes relleno para llegar a más."
    
    WRITER_WORD_COUNT_GUIDELINE = "Cada sección de curiosidad debe redactarse de forma muy concisa y al grano, entre 130 y 200 palabras. Evita totalmente rodeos, frases de relleno de IA y repeticiones (el artículo completo final debe tener entre 800-1200 palabras)."
    TARGET_WORD_COUNT = 1000
    
    WRITER_SOURCE_INSTRUCTION = "USO DE FUENTES: Usa el Dossier Maestro como tu fuente principal de información. Si el dossier no tiene suficientes detalles o no explica bien el contexto de una curiosidad/dato, PUEDES usar tu propio conocimiento experto VERÍDICO sobre el anime para enriquecer el artículo. CRÍTICO: Tu conocimiento propio debe ser sobre datos verificables, ampliamente documentados y reales. Prohibido inventar o alucinar datos falsos (como falsas inspiraciones de nombres, homenajes no confirmados o referencias ficticias a locaciones reales).\nSi describes un personaje, usa EXCLUSIVAMENTE la descripción que aparece en el Dossier o datos reales incuestionables de la obra. No inventes roles, relaciones ni habilidades.\nLos datos duros del anime (número de episodios, géneros, estudios, año) son INMUTABLES. Cópialos textualmente del Dossier sin modificar.\nPROHIBIDO presentar opiniones, especulaciones o interpretaciones subjetivas como hechos."
    
    WRITER_DEDUCTION_INSTRUCTION = "PROHIBIDO ESPECULAR Y MODO CONSERVADOR: Si decides usar tu propio conocimiento experto para añadir detalles, debes estar 100% SEGURO de su veracidad oficial. Queda terminantemente prohibido inventar o asumir detalles si no tienes evidencia histórica directa. Si no estás 100% seguro de un detalle específico (como la inspiración de un nombre, la referencia de una estación de tren, o un homenaje a otro autor), NO lo incluyas en absoluto."
    
    MAP_BLACKLIST_INSTRUCTION = """CRÍTICO - LISTA NEGRA: Descarta INMEDIATAMENTE cualquier dato que:
- Provenga de Instagram, TikTok, Reddit, Twitter, YouTube.
- Mencione seguidores, likes, views, posts, stories, hashtags.
- Mencione cosplay, fanarts o merchandising de nicho sin valor informativo.
NOTA: Para análisis y curiosidades, SÍ debes extraer análisis temáticos de la trama, conceptos filosóficos de la obra, recepción crítica, detalles de producción, impacto cultural e interpretaciones oficiales ampliamente aceptadas."""

    async def fetch_data(self) -> dict:
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
                return source_data
            print(f"--> Anime '{source_data.get('title')}' skipped: status={source_data.get('status')}, eps={episodes_val}, year={year_val}. Retrying...")
            
        raise Exception("Failed to fetch valid data for curiosidades")

    def get_tavily_query(self, clean_title: str, source_data: dict) -> str:
        return f'{clean_title} anime trivia easter eggs hidden facts'

    def check_dossier_quality(self, dossier: dict) -> bool:
        trivia = dossier.get("triviaList", [])
        if not isinstance(trivia, list) or len(trivia) < 3:
            print(f"--> Quality Gate FAILED: Only {len(trivia) if isinstance(trivia, list) else 0} trivia items found (min 3 required).")
            return False
        print(f"--> Quality Gate PASSED: triviaList={len(trivia)} items")
        return True

    def get_outline(self, dossier: dict, title: str) -> list:
        out = [f"Introducción: 5 Cosas que no sabías de {title}"]
        for j in range(1, 6):
            out.append(f"Curiosidad #{j}")
        return out
