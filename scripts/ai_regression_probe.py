import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any


DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_USERNAME = "student"
DEFAULT_PASSWORD = "Test1234A"
DEFAULT_DEVICE_ID = 1
DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_STREAM_TIMEOUT_SECONDS = 90


def _json_loads_or_text(raw: str) -> dict[str, Any] | list[Any] | str:
    if not raw:
        return ""
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
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> tuple[int, dict[str, Any] | list[Any] | str]:
    url = base_url.rstrip("/") + path
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
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return resp.getcode(), _json_loads_or_text(raw)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        return exc.code, _json_loads_or_text(raw)


def request_sse(
    base_url: str,
    path: str,
    *,
    token: str,
    body: dict[str, Any],
    timeout: int = DEFAULT_STREAM_TIMEOUT_SECONDS,
) -> tuple[int, list[dict[str, Any]] | dict[str, Any] | str]:
    url = base_url.rstrip("/") + path
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "text/event-stream",
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers=headers,
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            events: list[dict[str, Any]] = []
            current_event = "message"
            current_data: list[str] = []

            def flush_event() -> None:
                nonlocal current_event, current_data
                if not current_data:
                    current_event = "message"
                    return
                raw_data = "\n".join(current_data)
                events.append(
                    {
                        "event": current_event,
                        "data": _json_loads_or_text(raw_data),
                    }
                )
                current_event = "message"
                current_data = []

            for raw_line in resp:
                line = raw_line.decode("utf-8", errors="replace").rstrip("\r\n")
                if not line:
                    flush_event()
                    continue
                if line.startswith(":"):
                    continue
                if line.startswith("event:"):
                    current_event = line[len("event:") :].strip() or "message"
                    continue
                if line.startswith("data:"):
                    current_data.append(line[len("data:") :].lstrip())

            flush_event()
            return resp.getcode(), events
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        return exc.code, _json_loads_or_text(raw)


def login(base_url: str, username: str, password: str) -> tuple[int, str | None, dict[str, Any] | list[Any] | str]:
    status, payload = request_json(
        "POST",
        base_url,
        "/token",
        form={"username": username, "password": password},
    )
    token = payload.get("access_token") if status == 200 and isinstance(payload, dict) else None
    return status, token, payload


def detect_markdown_features(answer: str) -> list[str]:
    checks = {
        "heading": bool(re.search(r"(?m)^\s{0,3}#{1,6}\s+\S", answer)),
        "unordered_list": bool(re.search(r"(?m)^\s*[-*+]\s+\S", answer)),
        "ordered_list": bool(re.search(r"(?m)^\s*\d+\.\s+\S", answer)),
        "table": bool(re.search(r"(?m)^\|.+\|\s*$", answer)),
        "code_fence": "```" in answer,
        "math": "$$" in answer or bool(re.search(r"\$[^$\n]+\$", answer)),
        "mermaid": "```mermaid" in answer.lower(),
    }
    return [name for name, ok in checks.items() if ok]


def extract_citation_indexes(answer: str, max_index: int | None = None) -> list[int]:
    found: list[int] = []
    seen: set[int] = set()
    for match in re.finditer(r"\[(\d{1,2})\]", answer or ""):
        value = int(match.group(1))
        if value in seen:
            continue
        if max_index is not None and (value < 1 or value > max_index):
            continue
        seen.add(value)
        found.append(value)
    return found


def classify(status: str, message: str, details: dict[str, Any]) -> dict[str, Any]:
    return {"status": status, "message": message, "details": details}


def check_markdown_contract(
    base_url: str,
    token: str,
    device_id: int,
    strict_markdown: bool,
) -> dict[str, Any]:
    question = (
        "Please answer in Markdown only. Include: "
        "1) a level-2 heading, 2) three bullet points, and 3) a two-column table "
        "about greenhouse data observation tips."
    )
    status, payload = request_json(
        "POST",
        base_url,
        "/api/ai/science-assistant",
        token=token,
        body={
            "question": question,
            "device_id": device_id,
            "enable_deep_thinking": False,
            "enable_web_search": False,
        },
    )
    if status != 200 or not isinstance(payload, dict):
        return classify(
            "fail",
            "AI markdown contract request failed",
            {"http_status": status, "payload": payload},
        )

    answer = str(payload.get("answer") or "").strip()
    source = str(payload.get("source") or "")
    features = detect_markdown_features(answer)

    if not answer:
        return classify(
            "fail",
            "AI markdown contract returned empty answer",
            {"source": source, "features": features},
        )

    if features:
        return classify(
            "pass",
            "AI markdown contract returned Markdown markers",
            {
                "source": source,
                "features": features,
                "answer_preview": answer[:220],
            },
        )

    if strict_markdown:
        return classify(
            "fail",
            "No Markdown markers found in answer",
            {"source": source, "answer_preview": answer[:220]},
        )

    return classify(
        "warn",
        "No Markdown markers found; environment may be using fallback model path",
        {"source": source, "answer_preview": answer[:220]},
    )


def _validate_citation_alignment(answer: str, citations: list[dict[str, Any]]) -> dict[str, Any]:
    normalized = [item for item in citations if str(item.get("url") or "").strip()]
    indexes = extract_citation_indexes(answer, max_index=len(normalized) if normalized else None)
    expected = list(range(1, len(normalized) + 1))
    return {
        "indexes": indexes,
        "expected_indexes": expected,
        "citation_count": len(normalized),
        "all_urls_present": len(normalized) == len(citations),
        "is_contiguous": indexes == expected,
        "has_indexes": bool(indexes),
    }


def check_web_citation_alignment(
    base_url: str,
    token: str,
    device_id: int,
    strict_citations: bool,
) -> dict[str, Any]:
    question = (
        "Use web search and give 2-3 points on greenhouse climate education trends. "
        "If sources are used, cite each relevant sentence with [n]."
    )
    status, payload = request_json(
        "POST",
        base_url,
        "/api/ai/science-assistant",
        token=token,
        body={
            "question": question,
            "device_id": device_id,
            "enable_deep_thinking": False,
            "enable_web_search": True,
        },
    )
    if status != 200 or not isinstance(payload, dict):
        return classify(
            "fail",
            "AI web citation request failed",
            {"http_status": status, "payload": payload},
        )

    answer = str(payload.get("answer") or "")
    citations = payload.get("citations") or []
    if not isinstance(citations, list):
        citations = []

    validation = _validate_citation_alignment(answer, citations)
    details = {
        "source": payload.get("source"),
        "web_search_used": payload.get("web_search_used"),
        "web_search_notice": payload.get("web_search_notice"),
        **validation,
    }

    if validation["citation_count"] == 0:
        if strict_citations:
            return classify(
                "fail",
                "No citations returned when strict citation mode is enabled",
                details,
            )
        return classify(
            "warn",
            "No citations returned; cannot fully validate [n] alignment",
            details,
        )

    if validation["is_contiguous"] and validation["all_urls_present"]:
        return classify(
            "pass",
            "Citations are contiguous and aligned with [n] references",
            details,
        )

    return classify(
        "fail",
        "Citations are not aligned with [n] references",
        details,
    )


def check_conversation_reload_alignment(
    base_url: str,
    token: str,
    device_id: int,
    strict_citations: bool,
    keep_conversation: bool,
) -> dict[str, Any]:
    create_status, create_payload = request_json(
        "POST",
        base_url,
        "/api/ai/conversations",
        token=token,
        body={"title": f"ai-regression-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"},
    )
    if create_status != 200 or not isinstance(create_payload, dict):
        return classify(
            "fail",
            "Failed to create AI conversation",
            {"http_status": create_status, "payload": create_payload},
        )

    conversation_id = create_payload.get("id")
    if not isinstance(conversation_id, int):
        return classify(
            "fail",
            "Conversation creation response has no valid id",
            {"payload": create_payload},
        )

    result: dict[str, Any]
    try:
        stream_status, stream_payload = request_sse(
            base_url,
            f"/api/ai/conversations/{conversation_id}/science-assistant/stream",
            token=token,
            body={
                "question": (
                    "Use web search to explain greenhouse classroom climate changes in 2-3 points, "
                    "and cite evidence using [n]."
                ),
                "device_id": device_id,
                "enable_deep_thinking": False,
                "enable_web_search": True,
            },
        )
        if stream_status != 200 or not isinstance(stream_payload, list):
            return classify(
                "fail",
                "Conversation stream request failed",
                {"http_status": stream_status, "payload": stream_payload, "conversation_id": conversation_id},
            )

        token_parts: list[str] = []
        done_seen = False
        stream_errors: list[Any] = []
        for event in stream_payload:
            event_name = event.get("event")
            data = event.get("data")
            if event_name == "token" and isinstance(data, dict):
                piece = str(data.get("text") or "")
                if piece:
                    token_parts.append(piece)
            elif event_name == "done":
                done_seen = True
            elif event_name == "error":
                stream_errors.append(data)

        detail_status, detail_payload = request_json(
            "GET",
            base_url,
            f"/api/ai/conversations/{conversation_id}",
            token=token,
        )
        if detail_status != 200 or not isinstance(detail_payload, dict):
            return classify(
                "fail",
                "Failed to reload conversation detail",
                {
                    "http_status": detail_status,
                    "payload": detail_payload,
                    "conversation_id": conversation_id,
                    "done_seen": done_seen,
                },
            )

        messages = detail_payload.get("messages") or []
        assistant_messages = [m for m in messages if isinstance(m, dict) and m.get("role") == "assistant"]
        if not assistant_messages:
            return classify(
                "fail",
                "No assistant message found after stream conversation",
                {
                    "conversation_id": conversation_id,
                    "done_seen": done_seen,
                    "stream_error_count": len(stream_errors),
                },
            )

        final_message = assistant_messages[-1]
        final_answer = str(final_message.get("content") or "")
        final_citations = final_message.get("citations") or []
        if not isinstance(final_citations, list):
            final_citations = []

        validation = _validate_citation_alignment(final_answer, final_citations)
        details = {
            "conversation_id": conversation_id,
            "done_seen": done_seen,
            "stream_error_count": len(stream_errors),
            "stream_text_chars": len("".join(token_parts)),
            "persisted_answer_chars": len(final_answer),
            "persisted_source": final_message.get("source"),
            "persisted_web_notice": final_message.get("web_search_notice"),
            **validation,
        }

        if not final_answer.strip():
            return classify(
                "fail",
                "Persisted assistant answer is empty after stream",
                details,
            )

        if validation["citation_count"] == 0:
            if strict_citations:
                return classify(
                    "fail",
                    "No persisted citations found in strict citation mode",
                    details,
                )
            return classify(
                "warn",
                "No persisted citations found; reload alignment is inconclusive",
                details,
            )

        if validation["is_contiguous"] and validation["all_urls_present"] and done_seen:
            return classify(
                "pass",
                "Conversation reload kept [n] references aligned with persisted citations",
                details,
            )

        return classify(
            "fail",
            "Conversation reload citation alignment check failed",
            details,
        )
    finally:
        if not keep_conversation:
            request_json(
                "DELETE",
                base_url,
                f"/api/ai/conversations/{conversation_id}",
                token=token,
            )


def write_report(path: str, report: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(report, fp, ensure_ascii=False, indent=2)


def build_default_output_path() -> str:
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root_dir, "docs", "ai_regression_probe_results_latest.json")


def main() -> int:
    parser = argparse.ArgumentParser(description="Minimal AI assistant regression probe")
    parser.add_argument("--base-url", default=os.getenv("AI_PROBE_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--username", default=os.getenv("AI_PROBE_USERNAME", DEFAULT_USERNAME))
    parser.add_argument("--password", default=os.getenv("AI_PROBE_PASSWORD", DEFAULT_PASSWORD))
    parser.add_argument("--device-id", type=int, default=int(os.getenv("AI_PROBE_DEVICE_ID", DEFAULT_DEVICE_ID)))
    parser.add_argument("--strict-markdown", action="store_true")
    parser.add_argument("--strict-citations", action="store_true")
    parser.add_argument("--keep-conversation", action="store_true")
    parser.add_argument("--output", default=build_default_output_path())
    args = parser.parse_args()

    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "base_url": args.base_url,
        "username": args.username,
        "device_id": args.device_id,
        "strict_markdown": args.strict_markdown,
        "strict_citations": args.strict_citations,
        "cases": [],
    }

    login_status, token, login_payload = login(args.base_url, args.username, args.password)
    if not token:
        report["cases"].append(
            {
                "name": "login",
                **classify(
                    "fail",
                    "Login failed, cannot run AI regression probe",
                    {"http_status": login_status, "payload": login_payload},
                ),
            }
        )
        report["summary"] = {"pass": 0, "warn": 0, "fail": 1}
        write_report(args.output, report)
        print(f"report={args.output}")
        print("pass=0 warn=0 fail=1")
        return 2

    report["cases"].append(
        {
            "name": "markdown_contract",
            **check_markdown_contract(
                args.base_url,
                token,
                args.device_id,
                args.strict_markdown,
            ),
        }
    )
    report["cases"].append(
        {
            "name": "web_citation_alignment",
            **check_web_citation_alignment(
                args.base_url,
                token,
                args.device_id,
                args.strict_citations,
            ),
        }
    )
    report["cases"].append(
        {
            "name": "conversation_reload_alignment",
            **check_conversation_reload_alignment(
                args.base_url,
                token,
                args.device_id,
                args.strict_citations,
                args.keep_conversation,
            ),
        }
    )

    summary = {"pass": 0, "warn": 0, "fail": 0}
    for item in report["cases"]:
        status = str(item.get("status") or "fail")
        if status not in summary:
            status = "fail"
        summary[status] += 1

    report["summary"] = summary
    write_report(args.output, report)

    print(f"report={args.output}")
    for item in report["cases"]:
        print(f"[{str(item.get('status')).upper()}] {item.get('name')}: {item.get('message')}")
    print(f"pass={summary['pass']} warn={summary['warn']} fail={summary['fail']}")

    return 2 if summary["fail"] else 0


if __name__ == "__main__":
    raise SystemExit(main())