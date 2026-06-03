"""Unit tests for the live-content plumbing in PetController (overlays, takeovers,
agent tally). These exercise the data plumbing only — no render loop / bridge IO."""

import unittest
from pathlib import Path

from divoom_pet.daemon.bridge import DitooBridge
from divoom_pet.daemon.state_machine import PetController
from divoom_pet.render.compositor import CountBadge, ProgressBar


def _controller() -> PetController:
    # simulate=True bridge: no subprocess, no Bluetooth; we never start the loop.
    bridge = DitooBridge(Path("nonexistent"), mac="00:00:00:00:00:00", simulate=True)
    return PetController(bridge=bridge)


class OverlayTests(unittest.TestCase):
    def test_set_overlay_is_immutable_swap(self):
        c = _controller()
        before = c._overlays
        c.set_overlay("progress", ProgressBar(value=0.5))
        self.assertIsNot(c._overlays, before)  # new dict, not mutated in place
        self.assertIn("progress", c._overlays)

    def test_clear_one_overlay(self):
        c = _controller()
        c.set_overlay("progress", ProgressBar(value=0.5))
        c.set_overlay("badge", CountBadge(count=1))
        c.clear_overlay("progress")
        self.assertNotIn("progress", c._overlays)
        self.assertIn("badge", c._overlays)

    def test_clear_all_overlays(self):
        c = _controller()
        c.set_overlay("progress", ProgressBar(value=0.5))
        c.set_overlay("badge", CountBadge(count=1))
        c.clear_overlay()
        self.assertEqual(c._overlays, {})


class TakeoverTests(unittest.TestCase):
    def test_queue_and_consume(self):
        c = _controller()
        c.play_takeover([([(0, 0, 0)] * 256, 100)])
        self.assertIsNotNone(c._pop_takeover())
        self.assertIsNone(c._pop_takeover())  # consumed once

    def test_empty_takeover_ignored(self):
        c = _controller()
        c.play_takeover([])
        self.assertIsNone(c._pop_takeover())


class AgentTallyTests(unittest.TestCase):
    def test_increments_and_shows_badge(self):
        c = _controller()
        self.assertEqual(c.agent_came_home(), 1)
        self.assertEqual(c.agent_came_home(), 2)
        badge = c._overlays.get("badge")
        self.assertIsInstance(badge, CountBadge)
        self.assertEqual(badge.count, 2)

    def test_reset_zeroes_and_drops_badge(self):
        c = _controller()
        c.agent_came_home()
        c.reset_agents()
        self.assertEqual(c._agents_home, 0)
        self.assertNotIn("badge", c._overlays)


if __name__ == "__main__":
    unittest.main()
