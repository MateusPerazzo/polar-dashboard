"""Testes da mescla das personalizações com os padrões. Só dados fictícios."""

import unittest

import pandas as pd

from app.insights import build_insight
from app.settings import IMAGE_DEFAULTS, apply_colors, apply_image_style, apply_levels

GROUPS = {
    "sleep": {"title": "Sono", "color": "#111111"},
    "activity": {"title": "Atividade", "color": "#222222"},
}
LEVELS = {
    status: {"headline": f"Título {status}", "summary": f"Resumo {status}", "advice": f"Conselho {status}"}
    for status in range(1, 7)
}


class ApplyColorsTest(unittest.TestCase):
    def test_replaces_only_chosen_colors(self):
        merged = apply_colors(GROUPS, {"sleep": "#ff0000"})
        self.assertEqual(merged["sleep"], {"title": "Sono", "color": "#ff0000"})
        self.assertEqual(merged["activity"]["color"], "#222222")

    def test_invalid_color_keeps_default(self):
        for color in ["red", "#fff", "#gggggg", 123, None]:
            with self.subTest(color=color):
                self.assertEqual(apply_colors(GROUPS, {"sleep": color})["sleep"]["color"], "#111111")

    def test_defaults_are_not_changed(self):
        apply_colors(GROUPS, {"sleep": "#ff0000"})
        self.assertEqual(GROUPS["sleep"]["color"], "#111111")


class ApplyLevelsTest(unittest.TestCase):
    def test_replaces_only_chosen_fields(self):
        merged = apply_levels(LEVELS, {"3": {"headline": "Novo título"}})
        self.assertEqual(merged[3]["headline"], "Novo título")
        self.assertEqual(merged[3]["advice"], "Conselho 3")
        self.assertEqual(merged[4], LEVELS[4])

    def test_empty_and_unknown_fields_are_ignored(self):
        merged = apply_levels(LEVELS, {"3": {"headline": "  ", "advice": None, "extra": "x"}})
        self.assertEqual(merged[3], LEVELS[3])

    def test_defaults_are_not_changed(self):
        apply_levels(LEVELS, {"3": {"headline": "Novo título"}})
        self.assertEqual(LEVELS[3]["headline"], "Título 3")


class ApplyImageStyleTest(unittest.TestCase):
    def test_no_custom_values_gives_defaults(self):
        self.assertEqual(apply_image_style({}), IMAGE_DEFAULTS)

    def test_valid_values_are_used(self):
        custom = {"ratio": "1:1", "height": 300, "position": "top"}
        self.assertEqual(apply_image_style(custom), custom)

    def test_invalid_values_keep_defaults(self):
        for field, value in [("ratio", "2:1"), ("height", 1000), ("height", "300"), ("height", True),
                             ("position", "left"), ("position", "red; } body { display: none")]:
            with self.subTest(field=field, value=value):
                self.assertEqual(apply_image_style({field: value})[field], IMAGE_DEFAULTS[field])


class CustomLevelsInsightTest(unittest.TestCase):
    dates = pd.date_range("2026-01-01", periods=2)
    sleep = pd.DataFrame({"date": dates, "sleep_score": [70, 80]})

    def recharge(self, status):
        return pd.DataFrame({
            "date": self.dates,
            "heart_rate_variability_avg": [50, 55],
            "nightly_recharge_status": [4, status],
        })

    def test_uses_custom_messages(self):
        levels = apply_levels(LEVELS, {"2": {"headline": "Meu título"}})
        self.assertEqual(build_insight(self.sleep, self.recharge(2), levels=levels)["headline"], "Meu título")

    def test_missing_status_uses_custom_level_4(self):
        levels = apply_levels(LEVELS, {"4": {"summary": "Meu resumo"}})
        self.assertEqual(build_insight(self.sleep, self.recharge(None), levels=levels)["summary"], "Meu resumo")


if __name__ == "__main__":
    unittest.main()
