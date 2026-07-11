from .analisis import AnalisisStrategy
from .curiosidades import CuriosidadesStrategy
from .novedades import NovedadesStrategy
from .resenas import ResenasStrategy

def get_strategy(category: str):
    strategies = {
        'analisis': AnalisisStrategy(),
        'curiosidades': CuriosidadesStrategy(),
        'novedades': NovedadesStrategy(),
        'resenas': ResenasStrategy(),
    }
    if category not in strategies:
        raise ValueError(f"Unknown category: {category}")
    return strategies[category]
