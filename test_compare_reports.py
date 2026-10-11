"""Offline regression tests using invented measurements, not personal reports."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from compare_reports import compare_reports


def fixture():
    return {"results": [{
        "channel": "chromium", "headless": True,
        "browser_version": "example-version",
        "actual_host": {"system": "ExampleOS", "architecture": "example-arch"},
        "observed_browser": {"screen": {"width": 1280}, "deviceMemoryGiB": None,
                             "fontSampleWidths": {"Example Font": 120.0}},
        "measured_utc": "2026-01-01T00:00:00Z", "environment_id": "example",
        "repeat_sample_stable": True,
    }]}


class ComparisonTests(unittest.TestCase):
    def test_ignores_sampling_metadata_and_nested_samples(self):
        first = fixture()
        second = copy.deepcopy(first)
        second["results"][0].update(measured_utc="later", environment_id="changed",
                                    startup_observation={"measured_utc": "later"})
        self.assertTrue(compare_reports(first, second)["equal"])

    def test_detects_nested_measurement_and_mode_changes(self):
        first, second = fixture(), fixture()
        second["results"][0]["observed_browser"]["screen"]["width"] = 1920
        second["results"][0]["headless"] = False
        paths = {change["path"] for change in compare_reports(first, second)["changes"]}
        self.assertEqual(paths, {"headless", "observed_browser.screen.width"})

    def test_numeric_tolerance(self):
        first, second = fixture(), fixture()
        second["results"][0]["observed_browser"]["fontSampleWidths"]["Example Font"] += .01
        self.assertFalse(compare_reports(first, second)["equal"])
        self.assertTrue(compare_reports(first, second, .02)["equal"])

    def test_boolean_is_not_numeric(self):
        first, second = fixture(), fixture()
        second["results"][0]["headless"] = 1
        self.assertFalse(compare_reports(first, second, 100)["equal"])

    def test_missing_value_is_distinct_from_null(self):
        first, second = fixture(), fixture()
        del second["results"][0]["observed_browser"]["deviceMemoryGiB"]
        change = compare_reports(first, second)["changes"][0]
        self.assertTrue(change["before_present"])
        self.assertFalse(change["after_present"])

    def test_unavailable_channel_is_explicit(self):
        second = {"results": [{"channel": "chromium", "status": "unavailable",
                               "error_type": "ExampleError"}]}
        paths = {change["path"] for change in compare_reports(fixture(), second)["changes"]}
        self.assertIn("status", paths)
        self.assertIn("error_type", paths)

    def test_order_does_not_change_comparison(self):
        first = fixture()
        extra = copy.deepcopy(first["results"][0])
        extra["channel"] = "chrome"
        first["results"].append(extra)
        second = copy.deepcopy(first)
        second["results"].reverse()
        self.assertTrue(compare_reports(first, second)["equal"])

    def test_duplicate_channels_rejected(self):
        first = fixture()
        first["results"].append(copy.deepcopy(first["results"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate channel"):
            compare_reports(first, fixture())

    def test_invalid_input_rejected(self):
        for invalid in (None, {}, {"results": []}, {"results": [None]},
                        {"results": [{"channel": ""}]},
                        {"results": [{"channel": "chrome"}]}):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                compare_reports(invalid, fixture())
        for invalid in (-1, float("nan"), float("inf")):
            with self.subTest(tolerance=invalid), self.assertRaises(ValueError):
                compare_reports(fixture(), fixture(), invalid)

    def test_cli_exit_codes_and_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first, second = root / "a.json", root / "b.json"
            output = root / "nested" / "comparison.json"
            first.write_text(json.dumps(fixture()), encoding="utf-8")
            second.write_text(first.read_text(encoding="utf-8"), encoding="utf-8")
            command = [sys.executable, str(Path(__file__).with_name("compare_reports.py")),
                       str(first), str(second), "--output", str(output)]
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
            self.assertTrue(json.loads(output.read_text(encoding="utf-8"))["equal"])
            changed = fixture()
            changed["results"][0]["browser_version"] = "different-version"
            second.write_text(json.dumps(changed), encoding="utf-8")
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 1)
            second.write_text("not json", encoding="utf-8")
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 2)


if __name__ == "__main__":
    unittest.main()
