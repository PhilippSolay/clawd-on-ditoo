"""Unit tests for the ShuffleBag 'rotate randomly' selector."""

import unittest

from divoom_pet.sprites.rotation import ShuffleBag


class ShuffleBagTests(unittest.TestCase):
    def test_rejects_empty(self):
        with self.assertRaises(ValueError):
            ShuffleBag([])

    def test_single_item_always_returns_it(self):
        bag = ShuffleBag(["solo"])
        self.assertEqual([bag.draw() for _ in range(5)], ["solo"] * 5)

    def test_never_repeats_back_to_back(self):
        bag = ShuffleBag(["a", "b", "c"])
        draws = [bag.draw() for _ in range(300)]
        for i in range(1, len(draws)):
            self.assertNotEqual(draws[i], draws[i - 1], f"repeat at {i}: {draws[i]}")

    def test_every_pass_visits_all_items(self):
        # Draws come out in full passes: each chunk of len(items) is a permutation of
        # the whole set — so you always see the full variety before any repeat.
        items = ["jumprope", "tea", "boxing", "yoga"]
        bag = ShuffleBag(items)
        draws = [bag.draw() for _ in range(len(items) * 20)]
        for start in range(0, len(draws), len(items)):
            chunk = draws[start:start + len(items)]
            self.assertEqual(set(chunk), set(items), f"pass {chunk} missed an item")

    def test_two_items_alternate(self):
        bag = ShuffleBag(["x", "y"])
        draws = [bag.draw() for _ in range(20)]
        for i in range(1, len(draws)):
            self.assertNotEqual(draws[i], draws[i - 1])


class WiringTests(unittest.TestCase):
    def test_sport_selection_rotates_without_clumping(self):
        from divoom_pet.sprites.sports import SCENES, SPORT_ORDER, random_sport
        name_by_first_id = {id(scene[0][0]): name for name, scene in SCENES.items()}
        picks = [name_by_first_id[id(random_sport()[0][0])] for _ in range(len(SPORT_ORDER) * 6)]
        for i in range(1, len(picks)):
            self.assertNotEqual(picks[i], picks[i - 1], "sports clumped")
        self.assertEqual(set(picks), set(SPORT_ORDER), "not every activity appeared")

    def test_working_specials_rotate_without_clumping(self):
        from divoom_pet.sprites.coding import SCENES, WORK_SPECIALS, _WORK_BAG
        draws = [_WORK_BAG.draw() for _ in range(len(WORK_SPECIALS) * 8)]
        for i in range(1, len(draws)):
            self.assertNotEqual(draws[i], draws[i - 1], "working specials clumped")
        self.assertEqual(set(draws), set(WORK_SPECIALS))


if __name__ == "__main__":
    unittest.main()
