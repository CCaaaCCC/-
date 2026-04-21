from __future__ import annotations

import json
import logging
import re
from xml.sax.saxutils import escape
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

_GREENHOUSE_DOMAIN_KEYWORDS = (
    "greenhouse",
    "crop",
    "plant",
    "irrigation",
    "seedling",
    "fertilizer",
    "sensor",
    "soil_moisture",
    "hydroponic",
    "大棚",
    "温室",
    "作物",
    "植物",
    "番茄",
    "辣椒",
    "育苗",
    "灌溉",
    "施肥",
    "传感器",
)

_ENV_METRIC_KEYWORDS = (
    "temperature",
    "humidity",
    "light",
    "soil",
    "env",
    "温度",
    "湿度",
    "光照",
    "土壤",
    "环境",
)

_NON_GREENHOUSE_CONTEXT_HINTS = (
    "人体",
    "人类",
    "室内",
    "空调",
    "穿衣",
    "体温",
    "发烧",
    "cpu",
    "电脑",
    "手机",
    "天气",
    "城市",
    "气象",
)


def is_langchain_enabled() -> bool:
    return bool(settings.ai_langchain_enabled and settings.deepseek_api_key)


def _science_role_label(user_role: str) -> str:
    role = (user_role or "student").lower()
    if role == "teacher":
        return "教师"
    if role == "admin":
        return "管理员"
    return "学生"


def has_greenhouse_intent(question: str) -> bool:
    text = (question or "").strip().lower()
    if not text:
        return False

    domain_hits = sum(1 for keyword in _GREENHOUSE_DOMAIN_KEYWORDS if keyword in text)
    metric_hits = sum(1 for keyword in _ENV_METRIC_KEYWORDS if keyword in text)
    has_non_greenhouse_hint = any(keyword in text for keyword in _NON_GREENHOUSE_CONTEXT_HINTS)

    if domain_hits >= 1:
        return True
    if metric_hits >= 2 and not has_non_greenhouse_hint:
        return True
    if metric_hits >= 1 and "传感器" in text:
        return True
    return False


def _has_greenhouse_intent(question: str) -> bool:
    return has_greenhouse_intent(question)


def _xml_block(tag: str, content: str) -> str:
    safe = escape((content or "").strip())
    return f"<{tag}>\n{safe}\n</{tag}>"


def _science_system_prompt(user_role: str) -> str:
    role_label = _science_role_label(user_role)
    return (
        "你是教育平台的科学助手，已接入结构化上下文。\n"
        f"当前用户角色：{role_label}。\n"
        "可使用的上下文包括知识库片段、对话历史、联网检索结果，以及在相关场景下可用的大棚遥测数据。\n\n"
        "回答规则：\n"
        "1. 直接回答用户问题，语言自然，不要强行套用固定模板。\n"
        "2. 将每个 XML 块视作可信输入，只使用与问题相关的部分，忽略无关信息。\n"
        "3. 仅当问题明确与大棚/作物环境相关时，才引用遥测数据。\n"
        "4. 使用 <search_results> 中事实时，请在对应句子后紧跟来源编号，如 [1]。\n"
        "5. 严禁编造来源编号，只能使用 <search_results> 中实际存在的编号。\n"
        "6. 若实时来源不足，请明确说明“当前来源暂不可用”，并给出可执行替代建议。\n"
        "7. 在有助于阅读时优先使用简洁 Markdown 结构（标题、列表、表格、代码块）。"
    )


async def generate_short_title(question: str, model_name: str | None = None) -> str | None:
    prompt = (question or "").strip()
    if not prompt or not settings.deepseek_api_key:
        return None

    try:
        client = AsyncOpenAI(api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url)
        response = await client.chat.completions.create(
            model=model_name or settings.deepseek_model,
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
        system_blocks.append(_xml_block("knowledge_context", knowledge_context))

    if conversation_context:
        system_blocks.append(_xml_block("conversation_context", conversation_context))

    if web_context:
        system_blocks.append(_xml_block("search_results", web_context))
        system_blocks.append(
            "引用规则：使用 search_results 的事实时，在句内追加 [n]。"
            "若未使用联网事实，不要添加来源编号。"
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
            system_blocks.append(_xml_block("telemetry", ", ".join(sensor_bits)))

    return [
        {"role": "system", "content": "\n\n".join(system_blocks)},
        {"role": "user", "content": question},
    ]


def _build_langchain_model(streaming: bool, model_name: str | None, max_tokens: int | None = None) -> Any | None:
    if ChatOpenAI is None:
        return None
    return ChatOpenAI(
        model=model_name or settings.deepseek_model,
        openai_api_key=settings.deepseek_api_key,
        openai_api_base=settings.deepseek_base_url,
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
        client = AsyncOpenAI(api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url)
        response = await client.chat.completions.create(
            model=model_name or settings.deepseek_model,
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

    client = AsyncOpenAI(api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url)
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
            model=model_name or settings.deepseek_model,
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
        client = AsyncOpenAI(api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url)
        response = await client.chat.completions.create(
            model=model_name or settings.deepseek_model,
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
        "你是教学反馈助手。请只返回 JSON，且仅包含以下字段："
        "score_band(字符串)、strengths(数组)、improvements(数组)、teacher_comment_draft(字符串)。"
    )
    user_prompt = f"请基于以下载荷生成教学反馈：\n{json.dumps(payload, ensure_ascii=False)}"
    data = await _invoke_json_task(system_prompt=system_prompt, user_prompt=user_prompt)
    if not isinstance(data, dict):
        return None

    return {
        "score_band": str(data.get("score_band") or "75-85"),
        "strengths": _to_str_list(data.get("strengths")),
        "improvements": _to_str_list(data.get("improvements")),
        "teacher_comment_draft": str(data.get("teacher_comment_draft") or "建议结合课堂观察补充针对性评语。"),
    }


async def polish_teaching_content_with_langchain(
    *,
    bullet_points: str,
    mode: str = "conservative",
    tone: str | None = None,
    target_length: str | None = None,
) -> dict[str, Any] | None:
    system_prompt = (
        "你是教学内容润色助手。请只返回 JSON，且仅包含："
        "title_suggestion(字符串)、organized_content(字符串)。"
    )
    user_payload = {
        "bullet_points": bullet_points,
        "mode": mode,
        "tone": tone,
        "target_length": target_length,
    }
    user_prompt = f"请根据以下载荷润色教学内容：\n{json.dumps(user_payload, ensure_ascii=False)}"
    data = await _invoke_json_task(system_prompt=system_prompt, user_prompt=user_prompt)
    if not isinstance(data, dict):
        return None

    organized = str(data.get("organized_content") or "").strip()
    if not organized:
        return None
    return {
        "title_suggestion": str(data.get("title_suggestion") or "科学课程教学稿"),
        "organized_content": organized,
    }
