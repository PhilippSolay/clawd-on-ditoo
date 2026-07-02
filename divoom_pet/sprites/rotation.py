"""A tiny shuffle-bag for 'rotate randomly' selection.

Plain random.choice clumps — with 3 options it repeats the last pick ~1/3 of the
time, so you get "reading, reading, reading" and it reads as *not* rotating. A
ShuffleBag instead deals every option once in a random order, reshuffles when the
bag runs dry, and won't start a new pass with the item the last pass ended on. So
you always see the full variety, in a fresh random order, with no back-to-back
repeats.

Callers are the render loop's single thread (animation_for_state), so no locking.
"""

from __future__ import annotations

import random
from typing import List, Sequence


class ShuffleBag:
    def __init__(self, items: Sequence[str]) -> None:
        self._items: List[str] = list(items)
        if not self._items:
            raise ValueError("ShuffleBag needs at least one item")
        self._queue: List[str] = []   # remaining items this pass; we pop from the end
        self._last: str | None = None  # last item dealt, to avoid back-to-back repeats

    def draw(self) -> str:
        """Return the next item — a random order that visits every option before any
        repeats, and never the same item twice in a row."""
        if len(self._items) == 1:
            return self._items[0]
        if not self._queue:
            self._refill()
        pick = self._queue.pop()
        self._last = pick
        return pick

    def _refill(self) -> None:
        order = list(self._items)
        random.shuffle(order)
        # We pop from the end, so order[-1] is dealt first — keep it != the last item
        # of the previous pass so passes don't butt two identical picks together.
        if order[-1] == self._last and len(order) > 1:
            order[0], order[-1] = order[-1], order[0]
        self._queue = order
