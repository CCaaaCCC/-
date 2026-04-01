import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from typing import Any


BASE_URL = "http://127.0.0.1:8000"
TEST_PASSWORD = "Test1234A"


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
        qs = urllib.parse.urlencode(query)
        url = f"{url}?{qs}"

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
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, raw


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


def login(username: str) -> tuple[int, str | None, dict[str, Any] | str | list[Any]]:
    status, payload = request_json(
        "POST",
        "/token",
        form={"username": username, "password": TEST_PASSWORD},
    )
    token = None
    if status == 200 and isinstance(payload, dict):
        token = payload.get("access_token")
    return status, token, payload


def main() -> int:
    results: list[dict[str, Any]] = []

    # Anonymous access checks
    status, payload = request_json("GET", "/api/public/display")
    run_case(results, "anonymous_public_display", status, 200, payload)

    status, payload = request_json("GET", "/api/devices")
    run_case(results, "anonymous_devices_forbidden", status, 401, payload)

    # Login as all roles
    admin_status, admin_token, admin_payload = login("admin")
    run_case(results, "login_admin", admin_status, 200, admin_payload)

    teacher_status, teacher_token, teacher_payload = login("teacher")
    run_case(results, "login_teacher", teacher_status, 200, teacher_payload)

    student_status, student_token, student_payload = login("student")
    run_case(results, "login_student", student_status, 200, student_payload)

    if not (admin_token and teacher_token and student_token):
        write_results(results)
        return 1

    # Profile checks
    status, payload = request_json("GET", "/api/profile/me", token=admin_token)
    run_case(results, "profile_admin", status, 200, payload)

    status, payload = request_json("GET", "/api/profile/me", token=teacher_token)
    run_case(results, "profile_teacher", status, 200, payload)

    status, payload = request_json("GET", "/api/profile/me", token=student_token)
    run_case(results, "profile_student", status, 200, payload)

    student_class_id = None
    if isinstance(payload, dict):
        student_class_id = payload.get("class_id")

    # Permission checks
    status, payload = request_json("GET", "/api/users", token=student_token)
    run_case(results, "student_cannot_get_users", status, 403, payload)

    status, payload = request_json("POST", "/api/users", token=teacher_token, body={"username": "tmpx", "password": "Test1234A", "role": "student"})
    run_case(results, "teacher_cannot_create_users", status, 403, payload)

    status, payload = request_json("POST", "/api/control/1", token=student_token, body={"pump_state": 1})
    run_case(results, "student_cannot_control_device", status, 403, payload)

    status, payload = request_json("POST", "/api/control/1", token=teacher_token, body={"pump_state": 1, "fan_state": 1, "light_state": 1})
    run_case(results, "teacher_can_control_device", status, 200, payload)

    status, payload = request_json("GET", "/api/users", token=admin_token, query={"page": 1, "page_size": 20})
    run_case(results, "admin_get_users_paginated", status, 200, payload)

    # Assignment closed-loop
    now = datetime.now()
    start_date = now.strftime("%Y-%m-%d %H:%M:%S")
    due_date = (now + timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
    create_body = {
        "title": f"UX闭环测试任务-{now.strftime('%H%M%S')}",
        "description": "自动探测脚本创建",
        "class_id": student_class_id or 1,
        "device_id": 1,
        "requirement": "观察并记录环境变化",
        "start_date": start_date,
        "due_date": due_date,
        "is_published": True,
    }
    status, payload = request_json("POST", "/api/assignments", token=teacher_token, body=create_body)
    run_case(results, "teacher_create_assignment", status, 200, payload)

    assignment_id = payload.get("id") if isinstance(payload, dict) else None

    if assignment_id:
        status, payload = request_json("GET", "/api/assignments", token=student_token, query={"status": "all"})
        run_case(results, "student_list_assignments", status, 200, payload)

        submit_body = {
            "experiment_date": now.strftime("%Y-%m-%d"),
            "observations": "温度较稳定，土壤湿度略降。",
            "conclusion": "建议增加短时补水。",
        }
        status, payload = request_json("POST", f"/api/assignments/{assignment_id}/submit", token=student_token, body=submit_body)
        run_case(results, "student_submit_assignment", status, 200, payload)

        status, payload = request_json("GET", f"/api/assignments/{assignment_id}/submissions", token=teacher_token)
        run_case(results, "teacher_get_submissions", status, 200, payload)

        submission_id = None
        if isinstance(payload, list) and payload:
            submission_id = payload[0].get("id")

        if submission_id:
            grade_body = {"score": 92, "teacher_comment": "记录完整，结论清晰"}
            status, payload = request_json(
                "POST",
                f"/api/assignments/{assignment_id}/grade",
                token=teacher_token,
                body=grade_body,
                query={"submission_id": submission_id},
            )
            run_case(results, "teacher_grade_submission", status, 200, payload)

        status, payload = request_json("GET", f"/api/assignments/{assignment_id}/my-submission", token=student_token)
        run_case(results, "student_get_my_submission", status, 200, payload)

    # Export edge-case checks
    status, payload = request_json(
        "POST",
        "/api/telemetry/export",
        token=student_token,
        body={
            "device_id": 1,
            "start_date": (now - timedelta(days=40)).strftime("%Y-%m-%d"),
            "end_date": now.strftime("%Y-%m-%d"),
        },
    )
    run_case(results, "student_export_unbound_device_forbidden", status, 403, payload)

    status, payload = request_json(
        "POST",
        "/api/telemetry/export",
        token=teacher_token,
        body={"device_id": 1, "start_date": "2026-03-31", "end_date": "2026-03-32"},
    )
    run_case(results, "teacher_export_invalid_date_format", status, 400, payload)

    status, payload = request_json(
        "POST",
        "/api/telemetry/export",
        token=teacher_token,
        body={
            "device_id": 1,
            "start_date": (now - timedelta(days=40)).strftime("%Y-%m-%d"),
            "end_date": now.strftime("%Y-%m-%d"),
        },
    )
    run_case(results, "teacher_export_range_over_31_days", status, 400, payload)

    # AI assistant fallback behavior
    status, payload = request_json(
        "POST",
        "/api/ai/science-assistant",
        token=student_token,
        body={"question": "请判断当前环境是否适宜植物生长", "device_id": 1},
    )
    run_case(results, "ai_assistant_response", status, 200, payload)

    # Group module access (current implementation state)
    status, payload = request_json("GET", "/api/groups", token=student_token)
    run_case(results, "student_get_groups", status, [200, 403], payload)

    write_results(results)
    passed = sum(1 for item in results if item["pass"])
    print(f"passed={passed} total={len(results)}")
    return 0 if passed == len(results) else 2


def write_results(results: list[dict[str, Any]]) -> None:
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "ux_api_probe_results_2026-03-31.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(out_file)


if __name__ == "__main__":
    raise SystemExit(main())
