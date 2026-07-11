class BaseStrategy:
    # ---------------------------------------------------------
    # PROMPTS CONSTANTS (To be overridden by subclasses)
    # ---------------------------------------------------------
    REDUCE_JSON_FORMAT = "{}"
    REDUCE_EXTRA_INSTRUCTION = ""
    WRITER_WORD_COUNT_GUIDELINE = ""
    WRITER_SOURCE_INSTRUCTION = ""
    WRITER_DEDUCTION_INSTRUCTION = ""
    MAP_BLACKLIST_INSTRUCTION = ""
    TARGET_WORD_COUNT = 1000

    # ---------------------------------------------------------
    # METHODS (To be implemented by subclasses)
    # ---------------------------------------------------------
    async def fetch_data(self) -> dict:
        """Fetches the raw data from the corresponding API."""
        raise NotImplementedError

    def get_tavily_query(self, clean_title: str, source_data: dict) -> str:
        """Returns the search query string for Tavily."""
        raise NotImplementedError

    def check_dossier_quality(self, dossier: dict) -> bool:
        """Validates if the dossier has enough information to proceed."""
        raise NotImplementedError

    def get_outline(self, dossier: dict, title: str) -> list:
        """Returns the list of sections for the article."""
        raise NotImplementedError
