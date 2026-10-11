# Contributing

Browser Report Diff is an early-stage offline diagnostic tool. Improvements to
input validation, comparison semantics, error handling and documentation are welcome.

1. Open an issue with the problem and a minimal fictional example.
2. Make the change on a separate branch.
3. Add a regression test and run `python -m unittest discover -v`.
4. Submit a pull request explaining the behavior and validation.

Do not attach real diagnostic reports without first reviewing their OS/build,
renderer, languages, timezone and display measurements. Keep credentials,
browser profiles and unrelated private files out of issues and commits.

Tests must run with the Python standard library and no network access.
Code changes are contributed under this repository's MIT license.
