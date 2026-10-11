"""Compare two browser audit reports offline, ignoring sampling timestamps.

Exit codes: 0 = same measurements; 1 = differences; 2 = invalid input.
Uses only the Python standard library. Does not run a browser or make requests.
"""
import argparse
import json
import math
from pathlib import Path
import sys


FIELDS = (
    "actual_host", "browser_version", "channel", "headless",
    "preference_emulation", "user_agent_override", "observed_browser",
    "repeat_sample_stable", "cold_start_stable",
)
MISSING = object()


def _flatten(value, prefix=""):
    if isinstance(value, dict) and value:
        flattened = {}
        for key in sorted(value):
            name = f"{prefix}.{key}" if prefix else key
            flattened.update(_flatten(value[key], name))
        return flattened
    return {prefix: value}


def _index(report):
    if not isinstance(report, dict) or not isinstance(report.get("results"), list):
        raise ValueError("Report must be an object with a results array")
    if not report["results"]:
        raise ValueError("Report has no results")
    indexed = {}
    for result in report["results"]:
        if not isinstance(result, dict):
            raise ValueError("Each result must be an object")
        channel = result.get("channel")
        if not isinstance(channel, str) or not channel.strip():
            raise ValueError("Each result needs a non-empty channel")
        if channel in indexed:
            raise ValueError(f"Duplicate channel: {channel}")
        if result.get("status") == "unavailable":
            indexed[channel] = {
                "status": "unavailable", "error_type": result.get("error_type")
            }
        else:
            if not isinstance(result.get("actual_host"), dict):
                raise ValueError(f"Missing actual_host for {channel}")
            if not isinstance(result.get("observed_browser"), dict):
                raise ValueError(f"Missing observed_browser for {channel}")
            indexed[channel] = {"status": "available"}
            indexed[channel].update({key: result[key] for key in FIELDS if key in result})
    return indexed


def _equal(left, right, tolerance):
    if left is MISSING or right is MISSING:
        return left is right
    # A boolean is a mode setting, not the integer 0 or 1.
    if type(left) in (int, float) and type(right) in (int, float):
        return math.isclose(left, right, rel_tol=0, abs_tol=tolerance)
    return type(left) is type(right) and left == right


def compare_reports(before, after, tolerance=0.0):
    """Return changed measurement paths, preserving missing vs null values."""
    if not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError("Tolerance must be a finite non-negative number")
    left, right = _index(before), _index(after)
    changes = []
    for channel in sorted(left.keys() | right.keys()):
        first = _flatten(left[channel]) if channel in left else {}
        second = _flatten(right[channel]) if channel in right else {}
        for path in sorted(first.keys() | second.keys()):
            old, new = first.get(path, MISSING), second.get(path, MISSING)
            if not _equal(old, new, tolerance):
                changes.append({
                    "channel": channel, "path": path,
                    "before_present": old is not MISSING,
                    "after_present": new is not MISSING,
                    "before": None if old is MISSING else old,
                    "after": None if new is MISSING else new,
                })
    return {"schema_version": 1, "equal": not changes,
            "numeric_tolerance": tolerance, "changes": changes}


def _reject_constant(value):
    raise ValueError(f"Non-finite JSON number: {value}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("--tolerance", type=float, default=0.0,
                        help="Absolute tolerance for numeric measurements")
    parser.add_argument("--output", type=Path, help="Write the comparison as JSON")
    args = parser.parse_args(argv)
    try:
        reports = [json.loads(path.read_text(encoding="utf-8"),
                              parse_constant=_reject_constant)
                   for path in (args.before, args.after)]
        result = compare_reports(*reports, tolerance=args.tolerance)
        encoded = json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(encoded + "\n", encoding="utf-8")
            print(f"{len(result['changes'])} changed measurements; saved comparison")
        else:
            print(encoded)
        return 0 if result["equal"] else 1
    except (OSError, ValueError, TypeError) as error:
        print(f"Invalid report: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
