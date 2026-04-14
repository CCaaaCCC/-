from __future__ import annotations

import json
import logging
import re
from typing import Any, AsyncGenerator

from openai import AsyncOpenAI

from app.core.config import settings
from app.db.models import SensorReading

try:
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI
except Exception:  # pragma: no cover
    ChatPromptTemplate = None  # type: ignore[assignment]
    ChatOpenAI = None  # type: ignore[assignment]


logger = logging.getLogger(__name__)

_ENV_KEYWORDS = (
    "greenhouse",
    "sensor",
    "temperature",
    "humidity",
    "light",
    "soil",
    "env",
    "data",
    "\u5927\u68da",
    "\u73af\u5883",
    "\u6e29\u5ea6",
    "\u6e7f\u5ea6",
    "\u5149\u7167",
    "\u571f\u58e4",
    "\u4f20\u611f\u5668",
)


def is_langchain_enabled() -> bool:
    return bool(settings.ai_langchain_enabled and settings.qwen_api_key)


def _science_role_label(user_role: str) -> str:
    role = (user_role or "student").lower()
    if role == "teacher":
        return "teacher"
    if role == "admin":
        return "admin"
    return "student"


def _has_greenhouse_intent(question: str) -> bool:
    text = (question or "").lower()
    return any(keyword.lower() in text for keyword in _ENV_KEYWORDS)


def _science_system_prompt(user_role: str) -> str:
    role_label = _science_role_label(user_role)
    return (
        f"You are an AI assistant in an education platform. Current user role: {role_label}.\n"
        "Rules:\n"
        "1. Use natural and direct language.\n"
        "2. Do not force any fixed 3-part template unless user asks for it.\n"
        "3. Only mention greenhouse or sensor data when the user question is clearly related.\n"
        "4. If the question is unrelated to greenhouse context, answer directly and ignore sensor context.\n"
        "5. Format output in readable Markdown when appropriate (headings, lists, tables, code blocks).\n"
        "6. If web context is used, cite the source index like [1] right after the sentence. "
        "Use only indices that exist in provided context and do not fabricate references.\n"
        "7. Do not claim 'I cannot access the internet'. If real-time web data is missing, say it is temporarily unavailable and provide a practical fallback."
    )


async def generate_short_title(question: str, model_name: str | None = None) -> str | None:
    prompt = (question or "").strip()
    if not prompt or not settings.qwen_api_key:
        return None

    try:
        client = AsyncOpenAI(api_key=settings.qwen_api_key, base_url=settings.qwen_base_url)
        response = await client.chat.completions.create(
            model=model_name or settings.qwen_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是对话标题助手。请根据用户首条提问生成一个中文短标题。"
                        "要求：1) 8-18字；2) 不要标点；3) 不要引号；4) 只输出标题本身。"
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.2,
            max_tokens=32,
            stream=False,
        )
        return (response.choices[0].message.content or "").strip() or None
    except Exception as exc:  # pragma: no cover
        logger.warning("generate short title failed: %s", exc)
        return None


def _build_science_messages(
    question: str,
    latest: SensorReading | None,
    knowledge_context: str | None,
    conversation_context: str | None,
    web_context: str | None,
    user_role: str,
) -> list[dict[str, str]]:
    system_blocks = [_science_system_prompt(user_role)]

    if knowledge_context:
        system_blocks.append(f"Knowledge context:\n{knowledge_context}")

    if conversation_context:
        system_blocks.append(f"Conversation context:\n{conversation_context}")

    if web_context:
        system_blocks.append(f"Web context:\n{web_context}")
        system_blocks.append(
            "Citation rule: when you use web context facts, append source indices like [1] [2] in answer text. "
            "If no web fact is used, do not add any citation index."
        )

    if latest and _has_greenhouse_intent(question):
        sensor_bits: list[str] = []
        if latest.temp is not None:
            sensor_bits.append(f"temperature {latest.temp}C")
        if latest.humidity is not None:
            sensor_bits.append(f"humidity {latest.humidity}%")
        if latest.soil_moisture is not None:
            sensor_bits.append(f"soil_moisture {latest.soil_moisture}%")
        if latest.light is not None:
            sensor_bits.append(f"light {latest.light}lx")
        if sensor_bits:
            system_blocks.append("Current greenhouse data: " + ", ".join(sensor_bits))

    return [
        {"role": "system", "content": "\n\n".join(system_blocks)},
        {"role": "user", "content": question},
    ]


def _build_langchain_model(streaming: bool, model_name: str | None, max_tokens: int | None = None) -> ChatOpenAI | None:
    if ChatOpenAI is None:
        return None
    return ChatOpenAI(
        model=model_name or settings.qwen_model,
        openai_api_key=settings.qwen_api_key,
        openai_api_base=settings.qwen_base_url,
        temperature=settings.ai_temperature,
        max_tokens=max_tokens or settings.ai_max_tokens,
        timeout=settings.ai_stream_timeout_seconds if streaming else settings.ai_timeout_seconds,
        streaming=streaming,
    )


async def ask_science_with_langchain(
    question: str,
    latest: SensorReading | None,
    knowledge_context: str | None = None,
    conversation_context: str | None = None,
    web_context: str | None = None,
    user_role: str = "student",
    model_name: str | None = None,
    max_tokens: int | None = None,
) -> str | None:
    if not is_langchain_enabled() or not question.strip():
        return None

    messages = _build_science_messages(
        question,
        latest,
        knowledge_context,
        conversation_context,
        web_context,
        user_role,
    )

    model = _build_langchain_model(streaming=False, model_name=model_name, max_tokens=max_tokens)
    if model is not None and ChatPromptTemplate is not None:
        try:
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", "{system_text}"),
                    ("human", "{question}"),
                ]
            )
            chain = prompt | model
            response = await chain.ainvoke(
                {
                    "system_text": messages[0]["content"],
                    "question": question,
                }
            )
            content = str(response.content or "").strip()
            if content:
                return content
        except Exception as exc:  # pragma: no cover
            logger.warning("langchain ask failed, fallback to openai client: %s", exc)

    try:
        client = AsyncOpenAI(api_key=settings.qwen_api_key, base_url=settings.qwen_base_url)
        response = await client.chat.completions.create(
            model=model_name or settings.qwen_model,
            messages=messages,
            temperature=settings.ai_temperature,
            max_tokens=max_tokens or settings.ai_max_tokens,
            timeout=settings.ai_timeout_seconds,
            stream=False,
        )
        return (response.choices[0].message.content or "").strip() or None
    except Exception as exc:  # pragma: no cover
        logger.warning("openai ask failed: %s", exc)
        return None


async def stream_science_with_langchain(
    question: str,
    latest: SensorReading | None,
    knowledge_context: str | None = None,
    conversation_context: str | None = None,
    web_context: str | None = None,
    user_role: str = "student",
    model_name: str | None = None,
    max_tokens: int | None = None,
) -> AsyncGenerator[dict[str, str], None]:
    if not is_langchain_enabled() or not question.strip():
        return

    client = AsyncOpenAI(api_key=settings.qwen_api_key, base_url=settings.qwen_base_url)
    messages = _build_science_messages(
        question,
        latest,
        knowledge_context,
        conversation_context,
        web_context,
        user_role,
    )

    try:
        stream = await client.chat.completions.create(
            model=model_name or settings.qwen_model,
            messages=messages,
            temperature=settings.ai_temperature,
            max_tokens=max_tokens or settings.ai_max_tokens,
            timeout=settings.ai_stream_timeout_seconds,
            stream=True,
        )
        async for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            text = getattr(delta, "content", "") or ""
            reasoning = getattr(delta, "reasoning_content", "") or ""
            if text or reasoning:
                yield {"text": str(text), "reasoning": str(reasoning)}
    except Exception as exc:
        logger.warning("stream science with langchain failed: %s", exc)
        raise


def _extract_json_object(raw_text: str) -> dict[str, Any] | None:
    text = (raw_text or "").strip()
    if not text:
        return None

    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None
    try:
        obj = json.loads(match.group(0))
        if isinstance(obj, dict):
            return obj
    except Exception:
        return None
    return None


def _to_str_list(value: Any, max_len: int = 6) -> list[str]:
    if not isinstance(value, list):
        return []
    output: list[str] = []
    for item in value:
        text = str(item or "").strip()
        if text:
            output.append(text)
        if len(output) >= max_len:
            break
    return output


async def _invoke_json_task(
    *,
    system_prompt: str,
    user_prompt: str,
    model_name: str | None = None,
) -> dict[str, Any] | None:
    if not is_langchain_enabled():
        return None
    try:
        client = AsyncOpenAI(api_key=settings.qwen_api_key, base_url=settings.qwen_base_url)
        response = await client.chat.completions.create(
            model=model_name or settings.qwen_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=min(settings.ai_temperature, 0.3),
            max_tokens=max(settings.ai_max_tokens, 600),
            stream=False,
        )
        return _extract_json_object(response.choices[0].message.content or "")
    except Exception as exc:  # pragma: no cover
        logger.warning("invoke json task failed: %s", exc)
        return None


async def generate_assignment_feedback_with_langchain(payload: dict[str, Any]) -> dict[str, Any] | None:
    system_prompt = (
        "You are a teaching feedback assistant. Return JSON only with keys: "
        "score_band(string), strengths(array), improvements(array), teacher_comment_draft(string)."
    )
    user_prompt = f"Generate feedback from payload:\n{json.dumps(payload, ensure_ascii=False)}"
    data = await _invoke_json_task(system_prompt=system_prompt, user_prompt=user_prompt)
    if not isinstance(data, dict):
        return None

    return {
        "score_band": str(data.get("score_band") or "75-85"),
        "strengths": _to_str_list(data.get("strengths")),
        "improvements": _to_str_list(data.get("improvements")),
        "teacher_comment_draft": str(data.get("teacher_comment_draft") or "Please add comments with classroom observations."),
    }


async def polish_teaching_content_with_langchain(
    *,
    bullet_points: str,
    mode: str = "conservative",
    tone: str | None = None,
    target_length: str | None = None,
) -> dict[str, Any] | None:
    system_prompt = (
        "You are a content polishing assistant. Return JSON only with keys: "
        "title_suggestion(string), organized_content(string)."
    )
    user_payload = {
        "bullet_points": bullet_points,
        "mode": mode,
        "tone": tone,
        "target_length": target_length,
    }
    user_prompt = f"Polish the content from payload:\n{json.dumps(user_payload, ensure_ascii=False)}"
    data = await _invoke_json_task(system_prompt=system_prompt, user_prompt=user_prompt)
    if not isinstance(data, dict):
        return None

    organized = str(data.get("organized_content") or "").strip()
    if not organized:
        return None
    return {
        "title_suggestion": str(data.get("title_suggestion") or "Science Lesson Draft"),
        "organized_content": organized,
    }
