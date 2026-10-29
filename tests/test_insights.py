"""Testes das regras do Insight do dia e do hipnograma. Só dados fictícios."""

import unittest

import pandas as pd

from app.insights import build_insight, stage_segments

DATES = pd.date_range("2026-01-01", periods=8)


def fake_recharge(status):
    # 7 noites com HRV 50 e a última com 55: 10% acima da média.
    return pd.DataFrame({
        "date": DATES,
        "heart_rate_variability_avg": [50] * 7 + [55],
        "nightly_recharge_status": [4] * 7 + [status],
    })


class BuildInsightTest(unittest.TestCase):
    sleep = pd.DataFrame({"date": DATES, "sleep_score": [70] * 7 + [80]})

    def test_state_follows_recharge_status(self):
        for status, state in [(6, "good"), (5, "good"), (4, "neutral"), (2, "low")]:
            with self.subTest(status=status):
                self.assertEqual(build_insight(self.sleep, fake_recharge(status))["state"], state)

    def test_each_level_has_its_own_message_and_character(self):
        results = [build_insight(self.sleep, fake_recharge(status)) for status in range(1, 7)]
        self.assertEqual(len({result["headline"] for result in results}), 6)
        self.assertEqual(results[0]["character"], "Shikamaru")
        self.assertEqual(results[5]["character"], "Goku Super Saiyajin Blue")

    def test_missing_status_is_neutral(self):
        result = build_insight(self.sleep, fake_recharge(None))
        self.assertEqual(result["state"], "neutral")
        self.assertIsNone(result["status"])
        self.assertIsNone(result["character"])

    def test_text_mentions_hrv_and_sleep_score(self):
        text = build_insight(self.sleep, fake_recharge(4))["text"]
        self.assertIn("10% acima", text)
        self.assertIn("nota do sono foi 80", text)

    def test_past_night_uses_only_earlier_nights(self):
        recharge = fake_recharge(4)
        recharge.loc[2, "heart_rate_variability_avg"] = 70  # noite 03/01, 40% acima
        result = build_insight(self.sleep, recharge, DATES[2])
        self.assertEqual(result["date"], DATES[2])
        self.assertIn("Na noite de 03/01, seu HRV ficou 40% acima", result["text"])

    def test_no_data_returns_none(self):
        self.assertIsNone(build_insight(self.sleep, pd.DataFrame()))


class StageSegmentsTest(unittest.TestCase):
    def test_merges_light_stages_and_drops_unknown(self):
        times = pd.to_datetime(["2026-01-01 23:00", "2026-01-01 23:10", "2026-01-01 23:30",
                                "2026-01-02 00:10", "2026-01-02 00:20", "2026-01-02 00:30",
                                "2026-01-02 01:00"])
        hypnogram = pd.DataFrame({"timestamp": times, "stage": [2, 3, 4, 5, 0, 1, 1]})
        segments = stage_segments(hypnogram, pd.Timestamp("2026-01-02 01:30"))
        result = [(row.stage, f"{row.start:%H:%M}", f"{row.end:%H:%M}")
                  for row in segments.itertuples()]
        self.assertEqual(result, [
            ("Leve", "23:00", "23:30"),      # códigos 2 e 3 viram um trecho só
            ("Profundo", "23:30", "00:10"),
            ("Acordado", "00:20", "00:30"),  # o 5 (00:10-00:20) vira vão
            ("REM", "00:30", "01:30"),
        ])


if __name__ == "__main__":
    unittest.main()
