import argparse
import json
from pathlib import Path

import httpx


CASES_DIRECTORY = (
    Path(__file__).resolve().parents[1] / "tests" / "regression_cases"
)


def _matches(expected, actual):
    if isinstance(expected, dict):
        return all(key in actual and _matches(value, actual[key]) for key, value in expected.items())
    if isinstance(expected, list):
        return len(expected) == len(actual) and all(
            _matches(expected_value, actual_value)
            for expected_value, actual_value in zip(expected, actual)
        )
    return expected == actual


def main():
    parser = argparse.ArgumentParser(
        description="Run the 15 synthetic POs through a running ExceptionOS API."
    )
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument(
        "--output",
        default=str(CASES_DIRECTORY / "latest-results.json"),
    )
    arguments = parser.parse_args()

    cases = json.loads((CASES_DIRECTORY / "manifest.json").read_text(encoding="utf-8"))
    results = []
    with httpx.Client(timeout=120) as client:
        for case in cases:
            pdf_path = CASES_DIRECTORY / case["file"]
            with pdf_path.open("rb") as pdf_file:
                response = client.post(
                    f"{arguments.api_url}/purchase-orders/extract-pdf",
                    files={"file": (pdf_path.name, pdf_file, "application/pdf")},
                )
            actual = response.json() if response.is_success else None
            assessment = None
            issue_check_passed = True
            if response.is_success and not actual.get("missing_fields"):
                operational_order = {
                    key: value
                    for key, value in actual.items()
                    if key
                    not in {
                        "document_id",
                        "extraction_quality",
                        "missing_fields",
                    }
                    and value is not None
                }
                assessment_response = client.post(
                    f"{arguments.api_url}/purchase-orders/assess",
                    json=operational_order,
                )
                if assessment_response.is_success:
                    assessment = assessment_response.json()
                    expected_issues = set(case.get("expected_issues", []))
                    actual_issues = {
                        issue["reason"] for issue in assessment["issues"]
                    }
                    issue_check_passed = expected_issues <= actual_issues
                elif case.get("expected_issues"):
                    issue_check_passed = False
            results.append(
                {
                    "id": case["id"],
                    "title": case["title"],
                    "passed": response.is_success
                    and _matches(case["expected"], actual)
                    and issue_check_passed,
                    "status_code": response.status_code,
                    "expected": case["expected"],
                    "actual": actual,
                    "assessment": assessment,
                }
            )
            print(f"{case['id']}: {'PASS' if results[-1]['passed'] else 'FAIL'}")

    output_path = Path(arguments.output)
    output_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    passed = sum(result["passed"] for result in results)
    print(f"{passed}/{len(results)} cases passed. Results: {output_path}")


if __name__ == "__main__":
    main()
