import json
from pathlib import Path

import pymupdf


CASES_DIRECTORY = Path(__file__).with_name("regression_cases")


def test_regression_manifest_has_fifteen_distinct_cases():
    cases = json.loads(
        (CASES_DIRECTORY / "manifest.json").read_text(encoding="utf-8")
    )

    assert len(cases) == 15
    assert len({case["id"] for case in cases}) == 15
    assert all(case["depicts"] for case in cases)
    assert all(case["expected"] for case in cases)


def test_every_regression_case_has_a_readable_pdf():
    cases = json.loads(
        (CASES_DIRECTORY / "manifest.json").read_text(encoding="utf-8")
    )

    for case in cases:
        path = CASES_DIRECTORY / case["file"]
        assert path.is_file(), case["id"]
        with pymupdf.open(path) as document:
            assert document.page_count >= 1, case["id"]
