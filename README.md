# Browser Report Diff

Compare two browser diagnostic reports offline and see exactly which measurements
changed. A small Python command-line tool with **no third-party dependencies**.

Use it to compare exported browser environments between machines, operating systems
or browser upgrades. Changes are evidence to investigate, not a verdict that a
browser or device is incompatible.

Status: initial release, developed with AI assistance. External usage has not yet
been measured.

## Quick start

Download or clone this repository. With Python 3.11 or newer:

```bash
python compare_reports.py before.example.json after.example.json
python compare_reports.py before.example.json after.example.json --output outputs/comparison.json
```

The included examples are **fictional fixtures**, not measurements from anyone's
device. They demonstrate changes to a browser version and screen width.

No package or browser installation is required. On systems where Python is named
`python3`, use that command instead of `python`.

## What it compares

- Browser channel/version, execution OS and architecture.
- Headless mode and preference/user-agent override flags.
- Nested browser measurements: screen, graphics, fonts, canvas samples and preferences.
- Cold-start and warmed sample stability flags.
- Unavailable channels and their error types.

Sampling timestamps, derived environment IDs, explanatory notes and duplicate
startup/repeat sample objects are ignored. Arrays retain their order. Report
channels may appear in different orders; each report must contain at most one
result for each channel. A missing value remains distinct from an explicit JSON
`null`.

## Input format

The input is a JSON object with a non-empty `results` array. Available results need
a `channel`, `actual_host` object and `observed_browser` object. Other measurements
are optional. For example:

```json
{
  "results": [
    {
      "channel": "chromium",
      "browser_version": "example-version",
      "headless": true,
      "actual_host": {"system": "ExampleOS", "architecture": "example-arch"},
      "observed_browser": {"screen": {"width": 1280, "height": 720}}
    }
  ]
}
```

An unavailable result uses `{"channel": "chromium", "status": "unavailable",
"error_type": "ExampleError"}` instead of measurement objects. A single exported
observation must first be wrapped in `{"results": [observation]}`.

## Numeric tolerance and exit codes

```bash
python compare_reports.py before.json after.json --tolerance 0.02
python -m unittest discover -v
```

Tolerance is absolute and applies to numeric measurements only. It does not equate
booleans with `0` or `1`. Non-finite JSON numbers, invalid input and duplicate
channels are rejected.

| Exit code | Meaning |
| --- | --- |
| 0 | Measurements are equal |
| 1 | At least one measurement differs |
| 2 | Invalid input, invalid tolerance or file error |

Output JSON includes each changed path, its before/after value and flags indicating
whether those values were present. It can be consumed by another tool or a CI job.

## Tests and privacy

The test suite checks nested differences, metadata exclusion, tolerance, boolean
handling, missing/null values, channel ordering, unavailable results, invalid
reports and CLI exit codes. Tests use fictional data and the standard library.

The tool reads only the input paths you supply and writes the optional output path.
It does not launch a browser or send reports over the network. Reports can contain
device configuration information: inspect them before sharing, and keep local
reports out of commits. This is a diagnostic comparison tool, not a device identity
service or proof of physical hardware coverage.

Contributions are welcome; see [CONTRIBUTING.md](CONTRIBUTING.md).
Distributed under the [MIT license](LICENSE).
