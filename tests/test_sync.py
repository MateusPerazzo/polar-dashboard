"""Testes das conversões feitas na sincronização. Só dados fictícios, sem chamar a API."""

import unittest

from polar.sync import continuous_hr_rows, duration_seconds, night_series


class NightSeriesTest(unittest.TestCase):
    def test_times_after_midnight_go_to_next_day(self):
        rows = night_series("2026-01-02", "2026-01-01T23:00:00+02:00",
                            {"22:30": 52, "23:30": 50, "00:15": 48})
        self.assertEqual(rows, [
            ("2026-01-02", "2026-01-01T22:30", 52),  # até 1h antes do início: mesmo dia
            ("2026-01-02", "2026-01-01T23:30", 50),
            ("2026-01-02", "2026-01-02T00:15", 48),  # depois da meia-noite: dia seguinte
        ])


class ContinuousHrRowsTest(unittest.TestCase):
    def test_zero_readings_are_dropped(self):
        rows = continuous_hr_rows({"date": "2026-01-05", "heart_rate_samples": [
            {"sample_time": "13:39:40", "heart_rate": 72},
            {"sample_time": "13:39:41", "heart_rate": 0},  # sem leitura
            {"sample_time": "13:39:42", "heart_rate": 0},
            {"sample_time": "13:39:43", "heart_rate": 70},
        ]})
        self.assertEqual(rows, [
            ("2026-01-05", "2026-01-05T13:39:40", 72),
            ("2026-01-05", "2026-01-05T13:39:43", 70),
        ])

    def test_day_without_samples(self):
        self.assertEqual(continuous_hr_rows({"date": "2026-01-05"}), [])


class DurationSecondsTest(unittest.TestCase):
    def test_iso_8601_durations(self):
        self.assertEqual(duration_seconds("PT4H53M30S"), 17610)
        self.assertEqual(duration_seconds("PT45M"), 2700)
        self.assertEqual(duration_seconds("PT1.5S"), 1)

    def test_invalid_or_missing(self):
        self.assertIsNone(duration_seconds(None))
        self.assertIsNone(duration_seconds("4 horas"))


if __name__ == "__main__":
    unittest.main()
