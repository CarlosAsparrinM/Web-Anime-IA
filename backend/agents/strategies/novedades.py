from datetime import datetime
from .base import BaseStrategy
from agents.sources import fetch_anime_news

class NovedadesStrategy(BaseStrategy):
    REDUCE_JSON_FORMAT = """{
  "headline": "¿Qué ocurrió exactamente?",
  "whoAnnounced": "¿Quién lo anunció oficialmente?",
  "when": "Fecha del anuncio",
  "where": "Fuente oficial",
  "whyItMatters": "¿Por qué es importante?",
  "whatChanges": "¿Qué cambia respecto a antes?",
  "context": "Contexto del anime para nuevos lectores",
  "verifiedFacts": ["Dato verificado 1", "Dato verificado 2"]
}"""
    
    @property
    def REDUCE_EXTRA_INSTRUCTION(self):
        today_date = datetime.now().strftime("%Y-%m-%d")
        return f"HOY ES {today_date}. Esta es una noticia de ÚLTIMA HORA. NO conviertas rumores en hechos ni expectativas en anuncios. NO uses 'los fans esperan...' sin declaración oficial."
    
    WRITER_WORD_COUNT_GUIDELINE = "La sección debe tener aproximadamente entre 160 y 230 palabras (el artículo final será de 500-700 palabras)."
    TARGET_WORD_COUNT = 600
    
    WRITER_SOURCE_INSTRUCTION = "USO DE FUENTES: Usa el Dossier Maestro como tu ÚNICA fuente de información. QUEDA ESTRICTAMENTE PROHIBIDO inventar o deducir información, personajes, tramas, estudios, o fechas que no estén explícitamente en el Dossier. No uses tu 'conocimiento experto'. Si el Dossier tiene pocos datos, escribe una sección más corta, priorizando la veracidad absoluta sobre la longitud."
    
    WRITER_DEDUCTION_INSTRUCTION = "PROHIBIDO INTERPRETAR O DEDUCIR: Si el Dossier dice \"se anunció una película\", NO deduzcas que \"la serie dejará de existir\" o que \"reemplaza a la temporada 3\". Reporta SOLO lo que el Dossier dice literalmente. NUNCA presentes conclusiones lógicas como hechos confirmados. Si quieres mencionar una posibilidad, usa SIEMPRE frases como \"podría\", \"aún no se confirma\", \"queda por ver\"."
    
    MAP_BLACKLIST_INSTRUCTION = """CRÍTICO - LISTA NEGRA: Descarta INMEDIATAMENTE cualquier dato que:
- Provenga de Instagram, TikTok, Reddit, Twitter, YouTube.
- Sea una opinión, especulación o teoría de fans.
- Mencione seguidores, likes, views, posts, stories, hashtags.
- Mencione rumores, leaks, merchandising, cosplay o fanarts.
- Contenga frases como "podría", "se espera", "los fans creen"."""

    async def fetch_data(self) -> dict:
        source_data = await fetch_anime_news()
        if source_data:
            return source_data
        raise Exception("Failed to fetch valid data for novedades")

    def get_tavily_query(self, clean_title: str, source_data: dict) -> str:
        raw_news_title = source_data.get('title', clean_title)
        return f'"{raw_news_title}" anime latest news update official'

    def check_dossier_quality(self, dossier: dict) -> bool:
        has_headline = bool(dossier.get("headline"))
        has_facts = bool(dossier.get("verifiedFacts")) and len(dossier.get("verifiedFacts", [])) >= 1
        if not has_headline:
            print("--> Quality Gate FAILED: No headline found in dossier.")
            return False
        if not has_facts:
            print("--> Quality Gate FAILED: No verifiedFacts found in dossier.")
            return False
        print(f"--> Quality Gate PASSED: headline=OK, verifiedFacts={len(dossier.get('verifiedFacts', []))}")
        return True

    def get_outline(self, dossier: dict, title: str) -> list:
        return ["Titular y Resumen de la Noticia", "El Anuncio a Fondo", "Contexto del Anime"]
