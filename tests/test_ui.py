"""Testes da pílula de variação. Só dados fictícios."""

import unittest

from app.ui import pill


class PillTest(unittest.TestCase):
    def test_unit_pair_uses_singular_only_for_one(self):
        units = (" ponto", " pontos")
        self.assertIn("↑ 1 ponto<", pill(1.2, units, "up"))
        self.assertIn("↓ 1 ponto<", pill(-0.6, units, "up"))
        self.assertIn("↑ 2 pontos<", pill(1.6, units, "up"))
        self.assertIn("↑ 12 pontos<", pill(12, units, "up"))

    def test_rounded_zero_has_no_arrow_and_is_neutral(self):
        for delta in (0, 0.4, -0.4, 0.5):  # 0,5 arredonda para 0 (meio para o par)
            with self.subTest(delta=delta):
                html = pill(delta, " bpm", "down")
                self.assertNotIn("↑", html)
                self.assertNotIn("↓", html)
                self.assertIn("pill-neutral", html)
                self.assertIn(">0 bpm<", html)

    def test_zero_uses_plural(self):
        self.assertIn(">0 pontos<", pill(0.3, (" ponto", " pontos"), "up"))

    def test_plain_unit_is_kept(self):
        self.assertIn("↓ 3 bpm<", pill(-3, " bpm", "down"))

    def test_tone_follows_direction(self):
        self.assertIn("pill-good", pill(-3, " bpm", "down"))
        self.assertIn("pill-bad", pill(3, " bpm", "down"))
        self.assertIn("pill-neutral", pill(3, " kcal", "off"))

    def test_missing_delta(self):
        self.assertEqual(pill(None, " bpm", "down"), "")
        self.assertEqual(pill(float("nan"), " bpm", "down"), "")


if __name__ == "__main__":
    unittest.main()
