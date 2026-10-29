"""Testes das conversões feitas na sincronização. Só dados fictícios, sem chamar a API."""

import unittest

from polar.sync import duration_seconds, night_series


class NightSeriesTest(unittest.TestCase):
    def test_times_after_midnight_go_to_next_day(self):
        rows = night_series("2026-01-02", "2026-01-01T23:00:00+02:00",
                            {"22:30": 52, "23:30": 50, "00:15": 48})
        self.assertEqual(rows, [
            ("2026-01-02", "2026-01-01T22:30", 52),  # até 1h antes do início: mesmo dia
            ("2026-01-02", "2026-01-01T23:30", 50),
            ("2026-01-02", "2026-01-02T00:15", 48),  # depois da meia-noite: dia seguinte
        ])


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
