"""Human-like pacing tuned to minimize Amazon captcha triggers.

Default stays cautious; may rise to normal only after a long clean streak.
Relaxed is opt-in (max_mode) because the previous run captcha'd after entering relaxed.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class PaceState:
    mode: str = "cautious"  # cautious | normal | relaxed
    success_streak: int = 0
    risk_hits: int = 0
    pages_since_break: int = 0
    pages_since_session_cooldown: int = 0
    total_wait_s: float = 0.0
    page_waits: list[float] = field(default_factory=list)


# Seconds (min, max) after each page load, by mode — intentionally slower than before.
PAGE_DELAYS = {
    "cautious": (7.0, 14.0),
    "normal": (5.0, 9.0),
    "relaxed": (3.5, 6.5),
}

# Extra pause every N pages (min, max).
BREAK_EVERY = {
    "cautious": (3, (18.0, 35.0)),
    "normal": (5, (12.0, 22.0)),
    "relaxed": (7, (8.0, 15.0)),
}

COMBO_DELAYS = {
    "cautious": (8.0, 16.0),
    "normal": (5.0, 10.0),
    "relaxed": (3.0, 6.0),
}

# Full session cooldown (homepage + idle) every N successful pages.
SESSION_COOLDOWN_EVERY = {
    "cautious": (8, (45.0, 90.0)),
    "normal": (12, (35.0, 60.0)),
    "relaxed": (16, (25.0, 45.0)),
}

# Streak thresholds to promote (much stricter than before).
PROMOTE_TO_NORMAL_AFTER = 14
PROMOTE_TO_RELAXED_AFTER = 40


class HumanPacer:
    """Adaptive delay controller biased toward not triggering captcha."""

    def __init__(
        self,
        *,
        force_mode: str | None = None,
        max_mode: str = "normal",
        on_event: Callable[[str, dict], None] | None = None,
    ) -> None:
        start = force_mode or "cautious"
        self.state = PaceState(mode=start)
        self.max_mode = max_mode if max_mode in {"cautious", "normal", "relaxed"} else "normal"
        self._on_event = on_event
        self._rank = {"cautious": 0, "normal": 1, "relaxed": 2}

    @property
    def mode(self) -> str:
        return self.state.mode

    def _emit(self, event: str, **payload) -> None:
        if self._on_event:
            self._on_event(event, payload)
        else:
            extra = " ".join(f"{k}={v}" for k, v in payload.items())
            print(f"pace: {event} {extra}".strip(), flush=True)

    def _clamp_mode(self, mode: str) -> str:
        if self._rank[mode] > self._rank[self.max_mode]:
            return self.max_mode
        return mode

    def note_ok(self, *, got_new: bool) -> None:
        if got_new:
            self.state.success_streak += 1
        else:
            self.state.success_streak = max(0, self.state.success_streak - 2)

        old = self.state.mode
        if self.state.mode == "cautious" and self.state.success_streak >= PROMOTE_TO_NORMAL_AFTER:
            self.state.mode = self._clamp_mode("normal")
        elif self.state.mode == "normal" and self.state.success_streak >= PROMOTE_TO_RELAXED_AFTER:
            self.state.mode = self._clamp_mode("relaxed")

        if self.state.mode != old:
            self._emit(
                "mode_change",
                from_mode=old,
                to_mode=self.state.mode,
                streak=self.state.success_streak,
                max_mode=self.max_mode,
            )

    def note_risk(self, reason: str) -> None:
        self.state.risk_hits += 1
        self.state.success_streak = 0
        old = self.state.mode
        self.state.mode = "cautious"
        self._emit("risk", reason=reason, from_mode=old, to_mode="cautious")

    def wait_after_page(self) -> float:
        lo, hi = PAGE_DELAYS[self.state.mode]
        delay = random.uniform(lo, hi)
        if random.random() < 0.25:
            delay += random.uniform(2.0, 6.0)
        self.state.pages_since_break += 1
        self.state.pages_since_session_cooldown += 1

        every, (blo, bhi) = BREAK_EVERY[self.state.mode]
        if self.state.pages_since_break >= every:
            delay += random.uniform(blo, bhi)
            self.state.pages_since_break = 0
            self._emit("short_break", delay_s=round(delay, 2), mode=self.state.mode)

        time.sleep(delay)
        self.state.total_wait_s += delay
        self.state.page_waits.append(delay)
        return delay

    def needs_session_cooldown(self) -> bool:
        every, _ = SESSION_COOLDOWN_EVERY[self.state.mode]
        return self.state.pages_since_session_cooldown >= every

    def mark_session_cooldown_done(self, waited_s: float) -> None:
        self.state.pages_since_session_cooldown = 0
        self.state.total_wait_s += waited_s
        self._emit("session_cooldown", waited_s=round(waited_s, 2), mode=self.state.mode)

    def wait_between_combos(self) -> float:
        lo, hi = COMBO_DELAYS[self.state.mode]
        delay = random.uniform(lo, hi)
        # Keyword / filter switches are high-signal — always pad more.
        delay += random.uniform(2.0, 5.0)
        time.sleep(delay)
        self.state.total_wait_s += delay
        self._emit("combo_wait", delay_s=round(delay, 2), mode=self.state.mode)
        return delay

    def captcha_backoff(self) -> float:
        """Long cool-down before a single captcha retry."""
        delay = random.uniform(90.0, 150.0)
        self.note_risk("captcha_backoff")
        self._emit("captcha_backoff", delay_s=round(delay, 2))
        time.sleep(delay)
        self.state.total_wait_s += delay
        return delay

    def dwell_on_page(self, page) -> None:
        """Slower human-like scroll / idle on the loaded page."""
        try:
            scrolls = random.randint(2, 4)
            for _ in range(scrolls):
                page.mouse.wheel(0, random.randint(180, 650))
                page.wait_for_timeout(random.randint(400, 1400))
            if random.random() < 0.45:
                page.mouse.move(random.randint(80, 1000), random.randint(120, 700))
                page.wait_for_timeout(random.randint(300, 900))
            # Occasional longer read pause.
            if random.random() < 0.2:
                page.wait_for_timeout(random.randint(1500, 3500))
        except Exception:
            page.wait_for_timeout(random.randint(800, 2000))
