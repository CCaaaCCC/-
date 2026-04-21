import argparse
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any


DEFAULT_BASE_URL = 'http://127.0.0.1:8000'
DEFAULT_TEACHER_USERNAME = 'teacher'
DEFAULT_STUDENT_USERNAME = 'student'
DEFAULT_PASSWORD = 'Test1234A'


def _json_or_text(raw: str) -> dict[str, Any] | list[Any] | str:
    if not raw:
        return ''
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def request_json(
    method: str,
    base_url: str,
    path: str,
    *,
    token: str | None = None,
    body: dict[str, Any] | None = None,
    form: dict[str, str] | None = None,
    query: dict[str, Any] | None = None,
    timeout: int = 20,
) -> tuple[int, dict[str, Any] | list[Any] | str]:
    url = base_url.rstrip('/') + path
    if query:
        url = f"{url}?{urllib.parse.urlencode(query)}"

    headers: dict[str, str] = {}
    data: bytes | None = None

    if token:
        headers['Authorization'] = f'Bearer {token}'

    if body is not None:
        headers['Content-Type'] = 'application/json'
        data = json.dumps(body).encode('utf-8')
    elif form is not None:
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        data = urllib.parse.urlencode(form).encode('utf-8')

    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode('utf-8', errors='replace')
            return resp.getcode(), _json_or_text(raw)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode('utf-8', errors='replace')
        return exc.code, _json_or_text(raw)


def payload_preview(payload: dict[str, Any] | list[Any] | str) -> Any:
    if isinstance(payload, dict):
        keys = list(payload.keys())
        preview: dict[str, Any] = {'type': 'dict', 'keys': keys[:8]}
        if 'detail' in payload:
            preview['detail'] = payload.get('detail')
        if 'message' in payload:
            preview['message'] = payload.get('message')
        if 'items' in payload and isinstance(payload.get('items'), list):
            preview['items_count'] = len(payload['items'])
        return preview

    if isinstance(payload, list):
        return {'type': 'list', 'length': len(payload)}

    text = str(payload)
    return {'type': 'text', 'preview': text[:180]}


def login(base_url: str, username: str, password: str) -> tuple[int, str | None, dict[str, Any] | list[Any] | str]:
    status, payload = request_json(
        'POST',
        base_url,
        '/token',
        form={'username': username, 'password': password},
    )
    token = payload.get('access_token') if status == 200 and isinstance(payload, dict) else None
    return status, token, payload


def run_case(
    results: list[dict[str, Any]],
    *,
    name: str,
    status: int,
    expected: int | list[int],
    payload: dict[str, Any] | list[Any] | str,
) -> None:
    expected_list = expected if isinstance(expected, list) else [expected]
    results.append(
        {
            'name': name,
            'status': status,
            'expected': expected_list,
            'pass': status in expected_list,
            'payload_preview': payload_preview(payload),
        }
    )


def run_authenticated_suite(
    results: list[dict[str, Any]],
    *,
    role_prefix: str,
    base_url: str,
    token: str,
) -> None:
    common_cases: list[tuple[str, str, dict[str, Any] | None, int | list[int]]] = [
        ('profile_me', '/api/profile/me', None, 200),
        ('content_list', '/api/content/contents', {'page': 1, 'page_size': 20}, 200),
        ('assignments_list', '/api/assignments', {'status': 'all'}, 200),
    ]

    for case_name, path, query, expected in common_cases:
        status, payload = request_json('GET', base_url, path, token=token, query=query)
        run_case(
            results,
            name=f'{role_prefix}_{case_name}',
            status=status,
            expected=expected,
            payload=payload,
        )

    if role_prefix == 'teacher':
        teacher_cases: list[tuple[str, str, int | list[int]]] = [
            ('content_stats_overview', '/api/content/stats/overview', 200),
            ('content_stats_students', '/api/content/stats/students', 200),
        ]
        for case_name, path, expected in teacher_cases:
            status, payload = request_json('GET', base_url, path, token=token)
            run_case(
                results,
                name=f'{role_prefix}_{case_name}',
                status=status,
                expected=expected,
                payload=payload,
            )

    if role_prefix == 'student':
        student_cases: list[tuple[str, str, int | list[int]]] = [
            ('content_my_learning', '/api/content/my-learning', 200),
            ('content_stats_overview_forbidden', '/api/content/stats/overview', [401, 403]),
        ]
        for case_name, path, expected in student_cases:
            status, payload = request_json('GET', base_url, path, token=token)
            run_case(
                results,
                name=f'{role_prefix}_{case_name}',
                status=status,
                expected=expected,
                payload=payload,
            )


def build_default_output_path() -> str:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, 'docs', 'frontend_critical_api_probe_results_latest.json')


def write_report(path: str, report: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fp:
        json.dump(report, fp, ensure_ascii=False, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(description='Frontend critical API probe')
    parser.add_argument('--base-url', default=os.getenv('FRONTEND_PROBE_BASE_URL', DEFAULT_BASE_URL))
    parser.add_argument('--teacher-username', default=os.getenv('FRONTEND_PROBE_TEACHER_USERNAME', DEFAULT_TEACHER_USERNAME))
    parser.add_argument('--student-username', default=os.getenv('FRONTEND_PROBE_STUDENT_USERNAME', DEFAULT_STUDENT_USERNAME))
    parser.add_argument('--teacher-password', default=os.getenv('FRONTEND_PROBE_TEACHER_PASSWORD', DEFAULT_PASSWORD))
    parser.add_argument('--student-password', default=os.getenv('FRONTEND_PROBE_STUDENT_PASSWORD', DEFAULT_PASSWORD))
    parser.add_argument('--output', default=build_default_output_path())
    args = parser.parse_args()

    report: dict[str, Any] = {
        'generated_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'base_url': args.base_url,
        'teacher_username': args.teacher_username,
        'student_username': args.student_username,
        'cases': [],
    }

    teacher_login_status, teacher_token, teacher_login_payload = login(
        args.base_url,
        args.teacher_username,
        args.teacher_password,
    )
    run_case(
        report['cases'],
        name='teacher_login',
        status=teacher_login_status,
        expected=200,
        payload=teacher_login_payload,
    )

    student_login_status, student_token, student_login_payload = login(
        args.base_url,
        args.student_username,
        args.student_password,
    )
    run_case(
        report['cases'],
        name='student_login',
        status=student_login_status,
        expected=200,
        payload=student_login_payload,
    )

    if teacher_token:
        run_authenticated_suite(
            report['cases'],
            role_prefix='teacher',
            base_url=args.base_url,
            token=teacher_token,
        )

    if student_token:
        run_authenticated_suite(
            report['cases'],
            role_prefix='student',
            base_url=args.base_url,
            token=student_token,
        )

    summary = {'pass': 0, 'fail': 0}
    for case in report['cases']:
        if case.get('pass'):
            summary['pass'] += 1
        else:
            summary['fail'] += 1

    report['summary'] = summary
    write_report(args.output, report)

    print(f"report={args.output}")
    print(f"pass={summary['pass']} fail={summary['fail']}")

    return 0 if summary['fail'] == 0 else 2


if __name__ == '__main__':
    raise SystemExit(main())
