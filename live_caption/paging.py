"""Pure paging logic (no UI imports, so it can be unit tested).

Text is laid out left-to-right. The line fills up first; a new page starts
only when the next word would not fit in the remaining width.
"""

from typing import Callable, Dict, List, Sequence


class Paginator:
    def __init__(
        self,
        measure: Callable[[str], int],
        max_width: int,
        cache_limit: int = 3000,
    ):
        self._measure = measure
        self.max_width = max_width
        self.space_width = measure(" ")
        self._cache: Dict[str, int] = {}
        self._cache_limit = cache_limit

    def word_width(self, word: str) -> int:
        width = self._cache.get(word)
        if width is None:
            if len(self._cache) > self._cache_limit:
                self._cache.clear()
            width = self._measure(word)
            self._cache[word] = width
        return width

    def newest_page(self, words: Sequence[str]) -> List[str]:
        """Return the words of the NEWEST page."""
        page: List[str] = []
        used = 0
        for word in words:
            w = self.word_width(word)
            needed = w if not page else self.space_width + w
            if page and used + needed > self.max_width:
                page = [word]
                used = w
            else:
                page.append(word)
                used += needed
        return page
