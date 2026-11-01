"""Testes da mescla das personalizações com os padrões. Só dados fictícios."""

import unittest

import pandas as pd

from app.insights import build_insight
from app.settings import (DEFAULT_LOOK, apply_colors, apply_levels, apply_look, clamp_crop, crop_pixels,
                          default_crop, fit_crop, is_valid_crop)

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


class ApplyLookTest(unittest.TestCase):
    def test_defaults_when_nothing_saved(self):
        self.assertEqual(apply_look({}), DEFAULT_LOOK)

    def test_choices_are_independent(self):
        self.assertEqual(apply_look({"background": "light"}), {"background": "light", "cards": "gradient"})
        self.assertEqual(apply_look({"cards": "solid"}), {"background": "dark", "cards": "solid"})

    def test_unknown_values_keep_defaults(self):
        self.assertEqual(apply_look({"background": "red", "cards": None}), DEFAULT_LOOK)


class CropTest(unittest.TestCase):
    def test_valid_crop(self):
        self.assertTrue(is_valid_crop([0.1, 0.2, 0.5, 0.6]))
        for crop in [[0.5, 0, 0.6, 1],   # passa da borda direita
                     [0, 0, 0, 1],       # largura zero
                     [0, 0, 1], "0,0,1,1", [0, 0, True, 1], None]:
            with self.subTest(crop=crop):
                self.assertFalse(is_valid_crop(crop))

    def test_clamp_brings_box_inside_image(self):
        # O componente às vezes devolve um pouco além da borda (aqui, altura 1,0071).
        self.assertEqual(clamp_crop([0.1156, 0, 0.7469, 1.0071]), [0.1156, 0, 0.7469, 1])
        self.assertEqual(clamp_crop([-0.01, 0.5, 0.5, 0.6]), [0, 0.5, 0.5, 0.5])
        self.assertTrue(is_valid_crop(clamp_crop([0.6, 0.6, 0.5, 0.5])))

    def test_default_crop_is_largest_centered_box(self):
        # Imagem 2000x500 (4:1, mais larga que 16:9): usa a altura toda, no meio da largura.
        left, top, width, height = default_crop((2000, 500), (16, 9))
        self.assertEqual((top, height), (0, 1))
        self.assertAlmostEqual(width * 2000 / 500, 16 / 9)
        self.assertAlmostEqual(left, (1 - width) / 2)
        # Imagem 500x1000 (retrato): usa a largura toda, no meio da altura.
        left, top, width, height = default_crop((500, 1000), (16, 9))
        self.assertEqual((left, width), (0, 1))
        self.assertAlmostEqual(height * 1000 / 500, 9 / 16)
        self.assertAlmostEqual(top, (1 - height) / 2)

    def assertCropAlmostEqual(self, crop, expected):
        for value, wanted in zip(crop, expected):
            self.assertAlmostEqual(value, wanted, places=4)

    def test_fit_crop_keeps_center_and_width(self):
        # Moldura 16:9 de 800x450 px no meio de uma imagem 1600x900; em 3:2, a altura vai
        # para 533,3 px e o centro continua em y = 450 px.
        self.assertCropAlmostEqual(fit_crop([0.25, 0.25, 0.5, 0.5], (1600, 900), (3, 2)),
                                   [0.25, 183.333 / 900, 0.5, 533.333 / 900])

    def test_fit_crop_stays_inside_image(self):
        # Encostada no topo: a altura extra vai toda para baixo.
        self.assertCropAlmostEqual(fit_crop([0, 0, 0.5, 0.5], (1600, 900), (3, 2)),
                                   [0, 0, 0.5, 533.333 / 900])
        # Imagem inteira em 16:9: a altura não cabe, então usa a altura toda e estreita (1350 px).
        self.assertCropAlmostEqual(fit_crop([0, 0, 1, 1], (1600, 900), (3, 2)),
                                   [125 / 1600, 0, 1350 / 1600, 1])

    def test_fit_crop_keeps_crop_already_in_ratio(self):
        self.assertCropAlmostEqual(fit_crop([0.2, 0.3, 0.6, 0.4], (1000, 1000), (3, 2)),
                                   [0.2, 0.3, 0.6, 0.4])

    def test_crop_pixels(self):
        self.assertEqual(crop_pixels([0.25, 0, 0.5, 1], (1000, 500)), (250, 0, 750, 500))
        # Frações um pouco acima de 1 (arredondamento) não passam da borda.
        self.assertEqual(crop_pixels([0.5, 0, 0.5005, 1], (1000, 500)), (500, 0, 1000, 500))


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
