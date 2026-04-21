import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Any


BASE_URL = os.getenv("PROBE_BASE_URL", "http://127.0.0.1:8000")
TEST_PASSWORD = os.getenv("PROBE_TEST_PASSWORD", "Test1234A")


def request_json(
    method: str,
    path: str,
    token: str | None = None,
    body: dict[str, Any] | None = None,
    form: dict[str, str] | None = None,
    query: dict[str, Any] | None = None,
) -> tuple[int, dict[str, Any] | list[Any] | str]:
    url = BASE_URL + path
    if query:
        url = f"{url}?{urllib.parse.urlencode(query)}"

    headers: dict[str, str] = {}
    data: bytes | None = None

    if token:
        headers["Authorization"] = f"Bearer {token}"

    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    elif form is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        data = urllib.parse.urlencode(form).encode("utf-8")

    req = urllib.request.Request(url, data=data, method=method, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
            if not raw:
                return resp.getcode(), ""
            try:
                return resp.getcode(), json.loads(raw)
            except json.JSONDecodeError:
                return resp.getcode(), raw
    except urllib.error.HTTPError as err:
        raw = err.read().decode("utf-8")
        try:
            return err.code, json.loads(raw)
        except json.JSONDecodeError:
            return err.code, raw


def run_case(results: list[dict[str, Any]], name: str, status: int, expected: int | list[int], payload: Any) -> None:
    expected_list = expected if isinstance(expected, list) else [expected]
    ok = status in expected_list
    results.append(
        {
            "name": name,
            "status": status,
            "expected": expected_list,
            "pass": ok,
            "payload": payload,
        }
    )


def login(username: str) -> tuple[int, str | None, Any]:
    status, payload = request_json(
        "POST",
        "/token",
        form={"username": username, "password": TEST_PASSWORD},
    )
    token = payload.get("access_token") if status == 200 and isinstance(payload, dict) else None
    return status, token, payload


def probe_login_rate_limit(results: list[dict[str, Any]]) -> None:
    probe_user = f"rate_limit_probe_{int(time.time())}"

    for idx in range(1, 10):
        status, payload = request_json(
            "POST",
            "/token",
            form={"username": probe_user, "password": "wrong_password_for_probe"},
        )
        expected = 401 if idx <= 8 else 429
        run_case(results, f"login_rate_limit_attempt_{idx}", status, expected, payload)


def probe_pagination_guards(results: list[dict[str, Any]], token: str) -> None:
    checks = [
        ("content_page_zero_rejected", "/api/content/contents", {"page": 0}, 400),
        ("content_page_size_too_large_rejected", "/api/content/contents", {"page": 1, "page_size": 101}, 400),
        ("market_page_zero_rejected", "/api/market/products", {"page": 0}, 400),
        ("market_page_size_too_large_rejected", "/api/market/products", {"page": 1, "page_size": 101}, 400),
        (
            "assignments_page_zero_rejected",
            "/api/assignments",
            {"with_pagination": True, "page": 0, "page_size": 10, "status": "all"},
            400,
        ),
    ]

    for name, path, query, expected in checks:
        status, payload = request_json("GET", path, token=token, query=query)
        run_case(results, name, status, expected, payload)


def probe_assignments_compatibility(results: list[dict[str, Any]], token: str) -> None:
    status, payload = request_json("GET", "/api/assignments", token=token, query={"status": "all"})
    run_case(results, "assignments_legacy_list_shape", status, 200, payload)

    if status == 200:
        run_case(results, "assignments_legacy_is_list", 200 if isinstance(payload, list) else 500, 200, payload)

    status, payload = request_json(
        "GET",
        "/api/assignments",
        token=token,
        query={"status": "all", "with_pagination": True, "page": 1, "page_size": 5},
    )
    run_case(results, "assignments_paginated_shape", status, 200, payload)

    if status == 200:
        has_keys = isinstance(payload, dict) and {"items", "total", "page", "page_size"}.issubset(payload.keys())
        run_case(results, "assignments_paginated_has_meta", 200 if has_keys else 500, 200, payload)


def write_results(results: list[dict[str, Any]]) -> str:
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "stability_regression_probe_results_2026-04-19.json")
    with open(out_file, "w", encoding="utf-8") as handle:
        json.dump(results, handle, ensure_ascii=False, indent=2)
    return out_file


def main() -> int:
    results: list[dict[str, Any]] = []

    teacher_status, teacher_token, teacher_payload = login("teacher")
    run_case(results, "login_teacher", teacher_status, 200, teacher_payload)

    student_status, student_token, student_payload = login("student")
    run_case(results, "login_student", student_status, 200, student_payload)

    probe_login_rate_limit(results)

    if teacher_token:
        probe_pagination_guards(results, teacher_token)

    if student_token:
        probe_assignments_compatibility(results, student_token)

    out_file = write_results(results)
    passed = sum(1 for item in results if item["pass"])
    print(out_file)
    print(f"passed={passed} total={len(results)}")

    return 0 if passed == len(results) else 2


if __name__ == "__main__":
    raise SystemExit(main())
