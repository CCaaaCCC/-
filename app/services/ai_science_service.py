import json
import logging
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any, AsyncIterator, Optional

from app.core.config import settings
from app.db.models import SensorReading
from app.services.langchain_service import (
    ask_science_with_langchain,
    generate_short_title,
    generate_assignment_feedback_with_langchain,
    polish_teaching_content_with_langchain,
    stream_science_with_langchain,
)
from app.services.rag_service import search_teaching_content_context


SOURCE_RULE_BASED = "rule-based"
SOURCE_WEATHER_API = "weather-api"
MAX_WEB_SOURCES = 5
WEB_SEARCH_TIMEOUT_SECONDS = 8
WEATHER_API_TIMEOUT_SECONDS = 6
WEB_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
)
WEB_RESULT_BLOCKLIST = (
    "captcha",
    "cloudflare",
    "robot check",
    "human verification",
    "人机验证",
    "安全验证",
    "请完成验证",
    "请先登录",
)
WEB_QUERY_STOP_PHRASES = (
    "请你",
    "请帮我",
    "帮我",
    "给我",
    "写一篇",
    "生成一篇",
    "生成",
    "扩写",
    "整理",
    "一下",
)
WEB_QUERY_GENERIC_TERMS = {
    "什么",
    "怎么",
    "如何",
    "为什么",
    "一下",
    "相关",
    "介绍",
    "知识",
    "内容",
    "问题",
    "解释",
    "分析",
    "建议",
    "方法",
    "学习",
    "课堂",
    "科学",
}
WEB_AUTHORITY_HOST_HINTS = (
    ".gov.cn",
    ".edu.cn",
    ".ac.cn",
    "who.int",
    "fao.org",
    "edu.cn",
    "gov.cn",
    "wikipedia.org",
)
WEB_LOW_TRUST_HOST_HINTS = (
    "csdn.net",
    "zhihu.com",
    "toutiao.com",
    "sohu.com",
    "baijiahao.baidu.com",
)
WEB_MIN_RELEVANCE_SCORE = 0.11
WEB_MIN_COMBINED_SCORE = 0.17
SCIENCE_LONG_FORM_HINTS = (
    "教学资源",
    "教案",
    "课件",
    "课堂",
    "教学文章",
    "讲义",
    "完整",
    "详细",
    "扩写",
    "写一篇",
    "生成",
    "不少于",
    "字",
)

WEATHER_INTENT_KEYWORDS = (
    "天气",
    "气象",
    "weather",
    "forecast",
)

WEATHER_LOCATION_PREFIXES = (
    "请问",
    "帮我查",
    "查一下",
    "查",
    "帮我",
    "告诉我",
    "我想知道",
    "想知道",
)

WEATHER_CODE_TEXT: dict[int, str] = {
    0: "晴",
    1: "晴间多云",
    2: "多云",
    3: "阴",
    45: "雾",
    48: "雾凇",
    51: "小毛毛雨",
    53: "毛毛雨",
    55: "较强毛毛雨",
    56: "冻毛毛雨",
    57: "强冻毛毛雨",
    61: "小雨",
    63: "中雨",
    65: "大雨",
    66: "小冻雨",
    67: "强冻雨",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    77: "雪粒",
    80: "阵雨",
    81: "较强阵雨",
    82: "强阵雨",
    85: "阵雪",
    86: "强阵雪",
    95: "雷阵雨",
    96: "雷暴夹小冰雹",
    99: "雷暴夹大冰雹",
}

OFFLINE_CLAIM_PATTERN = re.compile(
    r"(我(?:目前|现在)?(?:无法|不能|不支持).{0,10}(?:联网|上网|访问互联网|访问网络)|"
    r"我(?:目前|现在)?(?:无法|不能).{0,16}(?:提供最新数据|获取实时(?:天气|数据)|提供实时(?:天气|数据))|"
    r"(?:没有|缺少).{0,12}实时(?:更新)?(?:的)?(?:天气|气象)?信息|"
    r"作为(?:一个)?ai[^。；\n]*(?:无法|不能).{0,16}(?:联网|上网|提供最新数据|获取实时(?:天气|数据)))",
    flags=re.IGNORECASE,
)


logger = logging.getLogger(__name__)


def _resolve_provider_source() -> str:
    model = (settings.qwen_model or "").lower()
    base_url = (settings.qwen_base_url or "").lower()
    if "deepseek" in model or "deepseek" in base_url:
        return "deepseek"
    if "qwen" in model or "dashscope" in base_url:
        return "qwen"
    return "llm"


SOURCE_QWEN = _resolve_provider_source()
SOURCE_LANGCHAIN = f"{SOURCE_QWEN}-langchain"
SOURCE_LANGCHAIN_RAG = f"{SOURCE_QWEN}-langchain-rag"


def _langchain_source(has_knowledge_context: bool) -> str:
    return SOURCE_LANGCHAIN_RAG if has_knowledge_context else SOURCE_LANGCHAIN


def _build_knowledge_context(question: str) -> tuple[str, bool]:
    context_rows = search_teaching_content_context(question, k=settings.rag_top_k)
    if not context_rows:
        return "", False

    knowledge_context = "\n".join(
        [f"{idx + 1}. {row['title']}：{row['snippet']}" for idx, row in enumerate(context_rows)]
    )
    return knowledge_context, True


def _conversation_to_text(conversation_history: Optional[list[dict[str, str]]]) -> str:
    if not conversation_history:
        return ""

    lines: list[str] = []
    for item in conversation_history[-10:]:
        role = str(item.get("role") or "user").lower()
        content = str(item.get("content") or "").strip()
        if not content:
            continue
        speaker = "用户" if role == "user" else "助手"
        lines.append(f"{speaker}：{content}")

    return "\n".join(lines)


def _science_role_label(user_role: str) -> str:
    role = (user_role or "student").lower()
    if role == "teacher":
        return "教师"
    if role == "admin":
        return "管理员"
    return "学生"


def _science_system_prompt_qwen(user_role: str) -> str:
    return (
        "你是一个人工智能助手。请用自然、易懂的语言客观回答问题，并优先使用 Markdown 组织内容（标题、列表、表格、代码块）。"
        "注意：仅当用户的提问涉及大棚、植物环境、传感器数据时，才结合提供的大棚数据给出分析。"
        "如果用户提问与此无关，请直接忽略该数据并回答问题。"
        "当系统提供联网参考且你使用了其中信息时，请在相关句子后添加来源编号（如 [1]、[2]），编号必须来自提供的参考列表，不要编造。"
        "若本次未拿到实时联网来源，请不要回答“我无法联网”；请改为“暂未获取到实时来源”，并给出可执行的替代建议。"
    )


def _resolve_science_model(enable_deep_thinking: bool) -> str:
    if enable_deep_thinking:
        return settings.ai_reasoner_model or settings.qwen_model or "deepseek-reasoner"
    return settings.ai_chat_model or settings.qwen_model or "deepseek-chat"


def _extract_target_length_from_question(question: str) -> int | None:
    text = (question or "").strip()
    if not text:
        return None

    match = re.search(r"(?:不少于|至少|约|大约)?\s*(\d{2,5})\s*(?:字|词|words?)", text, flags=re.IGNORECASE)
    if not match:
        return None

    return max(120, min(int(match.group(1)), 4000))


def _is_long_form_request(question: str) -> bool:
    text = (question or "").strip().lower()
    if not text:
        return False

    if any(keyword in text for keyword in SCIENCE_LONG_FORM_HINTS):
        return True

    plain_len = len(re.sub(r"\s+", "", text))
    return plain_len >= 120


def _resolve_science_max_tokens(question: str, enable_deep_thinking: bool) -> int:
    base_tokens = max(256, int(settings.ai_max_tokens))
    target_words = _extract_target_length_from_question(question)

    if target_words:
        estimated = int(target_words * 1.8)
        return max(base_tokens, min(estimated, 2600))

    if _is_long_form_request(question):
        return max(base_tokens, 1500 if enable_deep_thinking else 1200)

    if enable_deep_thinking:
        return max(base_tokens, 700)

    return base_tokens


def _fallback_conversation_title(question: str) -> str:
    title = re.sub(r"\s+", " ", (question or "").strip())
    title = title.replace("\n", " ").replace("\r", " ")
    title = title.strip("'\"“”‘’：:，,。！？!?. ")
    if not title:
        return "新对话"
    return title[:20]


def _sanitize_generated_title(raw: str | None) -> str:
    title = re.sub(r"\s+", " ", (raw or "").strip())
    title = title.split("\n", 1)[0]
    title = title.strip("'\"“”‘’：:，,。！？!?. ")
    if not title:
        return ""
    return title[:30]


async def generate_conversation_title(question: str) -> str:
    model_title = await generate_short_title(question, model_name=settings.ai_chat_model or settings.qwen_model)
    normalized = _sanitize_generated_title(model_title)
    if normalized:
        return normalized
    return _fallback_conversation_title(question)


def _clean_html_text(raw_text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", raw_text or "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _normalize_search_text(text: str) -> str:
    normalized = (text or "").lower().strip()
    normalized = re.sub(r"https?://\S+", " ", normalized)
    normalized = re.sub(r"[\s\u3000]+", " ", normalized)
    return normalized.strip()


def _extract_query_terms(question: str, max_terms: int = 8) -> list[str]:
    normalized = _normalize_search_text(question)
    if not normalized:
        return []

    tokens = re.findall(r"[a-z0-9]{2,}|[\u4e00-\u9fff]{2,}", normalized)
    terms: list[str] = []
    seen: set[str] = set()

    for token in tokens:
        if token in WEB_QUERY_GENERIC_TERMS:
            continue
        if token in seen:
            continue
        seen.add(token)
        terms.append(token)
        if len(terms) >= max_terms:
            break

    return terms


def _rewrite_web_search_query(question: str) -> str:
    query = _normalize_search_text(question)
    if not query:
        return ""

    for phrase in WEB_QUERY_STOP_PHRASES:
        query = query.replace(phrase, " ")

    query = re.sub(r"[\"'“”‘’`]+", " ", query)
    query = re.sub(r"\s+", " ", query).strip()
    if not query:
        return _normalize_search_text(question)[:120]
    return query[:120]


def _is_weather_query(question: str) -> bool:
    text = _normalize_search_text(question)
    if not text:
        return False

    if any(keyword in text for keyword in WEATHER_INTENT_KEYWORDS):
        return True

    return bool(re.search(r"(现在|今天|今日|目前).{0,14}(多少度|几度)", text))


def _clean_weather_location(raw: str) -> str:
    value = re.sub(r"\s+", " ", (raw or "")).strip(" ,，。?？!！:：")
    if not value:
        return ""

    lowered = value.lower()
    for prefix in WEATHER_LOCATION_PREFIXES:
        prefix_lower = prefix.lower()
        if lowered.startswith(prefix_lower):
            value = value[len(prefix):].strip()
            lowered = value.lower()

    value = re.sub(r"(?:现在|今天|今日|目前|此刻)$", "", value).strip(" ,，。?？!！:：")
    return value


def _extract_weather_location(question: str) -> str:
    text = (question or "").strip()
    if not text:
        return ""

    patterns = (
        r"([\u4e00-\u9fffA-Za-z·\-\s]{1,30}?)(?:现在|今天|今日|目前)?(?:的)?天气",
        r"(?:weather|forecast)\s+(?:in|for)\s+([A-Za-z][A-Za-z\s\-]{1,40})",
        r"([\u4e00-\u9fffA-Za-z·\-\s]{1,30}?)(?:现在|今天|今日|目前)?(?:多少度|几度)",
    )

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            continue
        location = _clean_weather_location(match.group(1))
        if location:
            return location

    return ""


def _fetch_json_payload(url: str, timeout: int) -> dict[str, Any]:
    request = urllib.request.Request(
        url=url,
        headers={
            "User-Agent": WEB_USER_AGENT,
            "Accept": "application/json, */*;q=0.8",
        },
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = response.read().decode("utf-8", errors="replace")
    return json.loads(payload)


def _format_weather_value(value: Any, unit: str, digits: int = 1) -> str:
    try:
        number = float(value)
        return f"{number:.{digits}f}{unit}"
    except (TypeError, ValueError):
        return f"未知{unit}" if unit else "未知"


def _weather_code_to_text(code: Any) -> str:
    try:
        normalized = int(code)
    except (TypeError, ValueError):
        return "未知"
    return WEATHER_CODE_TEXT.get(normalized, "未知")


def _pick_best_geocode_result(results: list[dict[str, Any]], location: str) -> dict[str, Any] | None:
    if not results:
        return None

    location_key = _normalize_search_text(location)
    best_item: dict[str, Any] | None = None
    best_score = float("-inf")

    for item in results:
        if not isinstance(item, dict):
            continue

        name = _normalize_search_text(str(item.get("name") or ""))
        admin1 = _normalize_search_text(str(item.get("admin1") or ""))
        country_code = str(item.get("country_code") or "").upper()
        feature_code = str(item.get("feature_code") or "").upper()

        try:
            population = float(item.get("population") or 0)
        except (TypeError, ValueError):
            population = 0.0

        score = 0.0
        if country_code == "CN":
            score += 1.6

        exact_aliases = {location_key}
        if location_key:
            exact_aliases.add(f"{location_key}市")

        if location_key and name in exact_aliases:
            score += 5.0
        elif location_key and name.startswith(location_key):
            score += 2.6
        elif location_key and location_key in name:
            score += 2.0

        if location_key and admin1 in exact_aliases:
            score += 1.5
        elif location_key and admin1 and location_key not in admin1:
            score -= 0.9

        if feature_code in {"PPLC", "PPLA", "PPLA2", "PPLA3", "PPL"}:
            score += 0.9
        if feature_code.startswith("ADM"):
            score -= 0.4

        score += min(population / 5_000_000.0, 3.0)

        if score > best_score:
            best_score = score
            best_item = item

    return best_item or results[0]


def _build_weather_location_queries(location: str) -> list[str]:
    base = _clean_weather_location(location)
    if not base:
        return []

    candidates = [base]
    if re.fullmatch(r"[\u4e00-\u9fff]{2,10}", base) and not base.endswith(("市", "区", "县", "州", "盟", "旗")):
        candidates.insert(0, f"{base}市")

    deduped: list[str] = []
    seen: set[str] = set()
    for item in candidates:
        key = _normalize_search_text(item)
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _try_build_weather_answer(question: str) -> tuple[str, list[dict[str, str]], str | None] | None:
    if not _is_weather_query(question):
        return None

    location = _extract_weather_location(question)
    if not location:
        return None

    try:
        geocode_results: list[dict[str, Any]] = []
        geocode_url = ""

        for location_query in _build_weather_location_queries(location):
            geocode_query = urllib.parse.urlencode(
                {
                    "name": location_query,
                    "count": 6,
                    "language": "zh",
                    "format": "json",
                }
            )
            geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?{geocode_query}"
            geocode_payload = _fetch_json_payload(geocode_url, timeout=WEATHER_API_TIMEOUT_SECONDS)
            query_results = geocode_payload.get("results") or []
            geocode_results.extend([item for item in query_results if isinstance(item, dict)])

        if not geocode_results:
            return None

        first = _pick_best_geocode_result(geocode_results, location)
        if not first:
            return None
        latitude = first.get("latitude")
        longitude = first.get("longitude")
        if latitude is None or longitude is None:
            return None

        place_name = str(first.get("name") or location).strip()
        country = str(first.get("country") or "").strip()
        admin1 = str(first.get("admin1") or "").strip()
        timezone_name = str(first.get("timezone") or "auto").strip() or "auto"

        forecast_query = urllib.parse.urlencode(
            {
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m",
                "timezone": "auto",
            }
        )
        forecast_url = f"https://api.open-meteo.com/v1/forecast?{forecast_query}"
        forecast_payload = _fetch_json_payload(forecast_url, timeout=WEATHER_API_TIMEOUT_SECONDS)
        current = forecast_payload.get("current") or {}
        if not current:
            return None

        weather_text = _weather_code_to_text(current.get("weather_code"))
        measure_time = str(current.get("time") or "未知")

        location_bits = [part for part in (place_name, admin1, country) if part]
        display_location = " / ".join(location_bits) if location_bits else place_name

        answer_lines = [
            f"以下是 {display_location} 的实时天气（数据时间 {measure_time}）[2]：",
            f"- 位置坐标：{_format_weather_value(latitude, '', 2)}, {_format_weather_value(longitude, '', 2)} [1]",
            f"- 天气现象：{weather_text}",
            f"- 气温：{_format_weather_value(current.get('temperature_2m'), '°C')}",
            f"- 体感温度：{_format_weather_value(current.get('apparent_temperature'), '°C')}",
            f"- 相对湿度：{_format_weather_value(current.get('relative_humidity_2m'), '%')}",
            f"- 降水量：{_format_weather_value(current.get('precipitation'), ' mm')}",
            f"- 风速：{_format_weather_value(current.get('wind_speed_10m'), ' km/h')}",
            "如果你愿意，我可以继续给你补充未来 24 小时趋势和出行建议。",
        ]

        citations = [
            {
                "title": f"Open-Meteo 地理编码：{display_location}",
                "url": geocode_url,
                "snippet": "用于把城市名解析为经纬度。",
            },
            {
                "title": f"Open-Meteo 实时天气：{display_location}",
                "url": forecast_url,
                "snippet": f"时区：{timezone_name}；时间：{measure_time}；天气：{weather_text}。",
            },
        ]
        return "\n".join(answer_lines), citations, "已获取实时天气数据来源。"
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        logger.warning("weather shortcut unavailable: %s", exc)
        return None


def _build_weather_fallback_answer(question: str) -> str:
    location = _extract_weather_location(question) or "该城市"
    return (
        f"我已尝试实时检索 {location} 的天气，但暂未拿到可用的实时来源。"
        "你可以稍后重试，或把城市名改成“中文名 + weather”再查一次。\n\n"
        "在等待实时数据时，可先参考通用建议：白天体感偏热时及时补水，"
        "早晚温差较大时注意增减衣物。"
    )


def _soften_offline_claim_for_weather(
    answer: str,
    question: str,
    citations: list[dict[str, str]],
    web_search_notice: str | None,
) -> tuple[str, list[dict[str, str]], str | None]:
    if not answer or not _is_weather_query(question):
        return answer, citations, web_search_notice

    if not OFFLINE_CLAIM_PATTERN.search(answer):
        return answer, citations, web_search_notice

    return (
        _build_weather_fallback_answer(question),
        [],
        "暂未获取到实时来源，已自动提供通用回答。",
    )


def _char_ngrams(text: str) -> set[str]:
    normalized = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", _normalize_search_text(text))
    if not normalized:
        return set()
    if len(normalized) == 1:
        return {normalized}
    return {normalized[idx: idx + 2] for idx in range(len(normalized) - 1)}


def _keyword_overlap_score(question: str, title: str, snippet: str) -> float:
    terms = _extract_query_terms(question)
    if not terms:
        return 0.0

    title_blob = _normalize_search_text(title)
    content_blob = _normalize_search_text(f"{title} {snippet}")

    title_hits = sum(1 for term in terms if term in title_blob)
    content_hits = sum(1 for term in terms if term in content_blob)

    title_score = title_hits / len(terms)
    content_score = content_hits / len(terms)
    return (title_score * 0.45) + (content_score * 0.55)


def _source_authority_score(title: str, url: str, snippet: str) -> float:
    host = urllib.parse.urlparse(url).netloc.lower()
    if not host:
        return 0.0

    score = 0.0
    if host.endswith((".gov.cn", ".edu.cn", ".ac.cn")):
        score += 0.34
    elif host.endswith((".org", ".org.cn")):
        score += 0.12

    if any(hint in host for hint in WEB_AUTHORITY_HOST_HINTS):
        score += 0.2

    if any(hint in host for hint in WEB_LOW_TRUST_HOST_HINTS):
        score -= 0.24

    trust_blob = f"{title} {snippet}".lower()
    if any(keyword in trust_blob for keyword in ("官网", "官方", "标准", "指南", "白皮书")):
        score += 0.08

    return max(-0.28, min(score, 0.46))


def _source_relevance_score(question: str, title: str, snippet: str) -> float:
    question_grams = _char_ngrams(question)
    keyword_score = _keyword_overlap_score(question, title, snippet)
    if not question_grams:
        return keyword_score

    title_grams = _char_ngrams(title)
    content_grams = _char_ngrams(f"{title} {snippet}")
    if not title_grams and not content_grams:
        return keyword_score

    title_score = len(question_grams & title_grams) / len(question_grams) if title_grams else 0.0
    content_score = len(question_grams & content_grams) / len(question_grams) if content_grams else 0.0
    return max(keyword_score, (title_score * 0.25) + (content_score * 0.45) + (keyword_score * 0.3))


def _is_low_quality_source(title: str, url: str, snippet: str) -> bool:
    blob = f"{title} {url} {snippet}".lower()
    return any(keyword in blob for keyword in WEB_RESULT_BLOCKLIST)


def _fetch_bing_rss_sources(query: str, max_results: int) -> list[dict[str, str]]:
    if not query:
        return []

    params = urllib.parse.urlencode(
        {
            "q": query,
            "format": "rss",
            "setlang": "zh-hans",
        }
    )
    url = f"https://www.bing.com/search?{params}"
    request = urllib.request.Request(
        url=url,
        headers={
            "User-Agent": WEB_USER_AGENT,
            "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8",
        },
        method="GET",
    )

    with urllib.request.urlopen(request, timeout=WEB_SEARCH_TIMEOUT_SECONDS) as response:
        payload = response.read()

    root = ET.fromstring(payload)
    sources: list[dict[str, str]] = []

    for item in root.findall("./channel/item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        snippet = _clean_html_text(item.findtext("description") or "")

        if not title or not link or not link.startswith("http"):
            continue

        sources.append(
            {
                "title": title[:120],
                "url": link,
                "snippet": snippet[:220],
            }
        )
        if len(sources) >= max_results:
            break

    return sources


def _search_web_sources(question: str, max_results: int = MAX_WEB_SOURCES) -> tuple[list[dict[str, str]], str | None]:
    raw_query = (question or "").strip()
    if not raw_query:
        return [], None

    rewritten_query = _rewrite_web_search_query(raw_query)
    fetch_limit = max(max_results * 4, max_results)

    try:
        candidates = _fetch_bing_rss_sources(rewritten_query, max_results=fetch_limit)
        if rewritten_query != raw_query and len(candidates) < max_results:
            candidates.extend(_fetch_bing_rss_sources(raw_query, max_results=fetch_limit))

        if not candidates:
            return [], "暂未获取到实时来源，已自动提供通用回答。"

        seen_urls: set[str] = set()
        seen_hosts: set[str] = set()
        scored: list[tuple[float, float, str, dict[str, str]]] = []

        for item in candidates:
            title = str(item.get("title") or "").strip()
            link = str(item.get("url") or "").strip()
            snippet = str(item.get("snippet") or "").strip()
            if not title or not link or not link.startswith("http"):
                continue
            if link in seen_urls:
                continue
            if _is_low_quality_source(title, link, snippet):
                continue

            relevance = _source_relevance_score(raw_query, title, snippet)
            if relevance < WEB_MIN_RELEVANCE_SCORE:
                continue

            authority = _source_authority_score(title, link, snippet)
            combined_score = relevance + authority
            if combined_score < WEB_MIN_COMBINED_SCORE and relevance < WEB_MIN_RELEVANCE_SCORE * 1.8:
                continue

            host = urllib.parse.urlparse(link).netloc.lower()
            scored.append(
                (
                    combined_score,
                    relevance,
                    host,
                    {
                        "title": title[:120],
                        "url": link,
                        "snippet": snippet[:220],
                    },
                )
            )
            seen_urls.add(link)

        if not scored:
            return [], "暂未检索到高相关来源，已自动提供通用回答。"

        scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
        selected: list[dict[str, str]] = []
        for combined_score, relevance, host, item in scored:
            if combined_score < WEB_MIN_COMBINED_SCORE and len(selected) >= 2:
                continue

            if host and host in seen_hosts and len(selected) >= 2:
                continue

            selected.append(item)
            if host:
                seen_hosts.add(host)
            if len(selected) >= max_results:
                break

        if not selected:
            selected = [item for _, _, _, item in scored[:max_results]]

        if selected:
            return selected, "已启用智能搜索，已按相关性与来源可信度筛选结果。"
        return [], "暂未检索到高相关来源，已自动提供通用回答。"
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ET.ParseError, ValueError) as exc:
        logger.warning("web search unavailable: %s", exc)
        return [], "暂未获取到实时来源，已自动提供通用回答。"


def _build_web_context(sources: list[dict[str, str]]) -> str:
    if not sources:
        return ""

    rows: list[str] = []
    for idx, item in enumerate(sources, start=1):
        title = str(item.get("title") or "来源")
        url = str(item.get("url") or "")
        snippet = str(item.get("snippet") or "暂无摘要")
        if not url:
            continue
        rows.append(f"[{idx}] {title}\n链接：{url}\n摘要：{snippet}")
    return "\n\n".join(rows)


def _extract_citation_indexes(answer: str, max_index: int) -> list[int]:
    if not answer or max_index <= 0:
        return []

    indexes: list[int] = []
    seen: set[int] = set()
    for match in re.finditer(r"\[(\d{1,2})\]", answer):
        value = int(match.group(1))
        if value < 1 or value > max_index or value in seen:
            continue
        seen.add(value)
        indexes.append(value)
    return indexes


def _rewrite_answer_citation_indexes(answer: str, indexes: list[int]) -> str:
    if not answer or not indexes:
        return answer

    remap = {old_index: new_index for new_index, old_index in enumerate(indexes, start=1)}

    def _replace(match: re.Match[str]) -> str:
        old_value = int(match.group(1))
        new_value = remap.get(old_value)
        if not new_value:
            return match.group(0)
        return f"[{new_value}]"

    return re.sub(r"\[(\d{1,2})\]", _replace, answer)


def align_citations_with_answer(
    answer: str,
    citations: list[dict[str, str]],
    web_search_notice: str | None,
) -> tuple[str, list[dict[str, str]], str | None]:
    normalized = [item for item in citations[:MAX_WEB_SOURCES] if str(item.get("url") or "").strip()]
    if not normalized:
        return answer, [], web_search_notice

    indexes = _extract_citation_indexes(answer, len(normalized))
    if not indexes:
        return answer, [], "已启用智能搜索，但回答未标注来源编号 [n]，本次不展示链接。"

    filtered = [normalized[index - 1] for index in indexes]
    if not filtered:
        return answer, [], "已启用智能搜索，但回答未标注有效来源编号，本次不展示链接。"

    aligned_answer = _rewrite_answer_citation_indexes(answer, indexes)
    return aligned_answer, filtered, "已启用智能搜索，仅展示回答中引用的高相关来源。"


def _build_science_response_meta(
    *,
    model_name: str,
    enable_deep_thinking: bool,
    enable_web_search: bool,
    citations: list[dict[str, str]],
    web_search_notice: str | None,
) -> dict[str, Any]:
    normalized: list[dict[str, str | None]] = []
    for item in citations[:MAX_WEB_SOURCES]:
        title = str(item.get("title") or "").strip()
        url = str(item.get("url") or "").strip()
        snippet = str(item.get("snippet") or "").strip()
        if not url:
            continue
        normalized.append(
            {
                "title": title or url,
                "url": url,
                "snippet": snippet or None,
            }
        )

    return {
        "model": model_name,
        "deep_thinking": bool(enable_deep_thinking),
        "web_search_enabled": bool(enable_web_search),
        "web_search_used": bool(enable_web_search and normalized),
        "web_search_notice": web_search_notice if enable_web_search else None,
        "citations": normalized,
    }


async def _ask_science_assistant_with_context(
    question: str,
    latest: Optional[SensorReading],
    knowledge_context: str,
    has_knowledge_context: bool,
    conversation_history: Optional[list[dict[str, str]]] = None,
    user_role: str = "student",
    model_name: str | None = None,
    web_context: str | None = None,
    max_tokens_override: int | None = None,
) -> tuple[str, str]:
    langchain_answer = await ask_science_with_langchain(
        question,
        latest,
        knowledge_context=knowledge_context,
        conversation_context=_conversation_to_text(conversation_history),
        web_context=web_context,
        user_role=user_role,
        model_name=model_name,
        max_tokens=max_tokens_override,
    )
    if langchain_answer:
        return langchain_answer, _langchain_source(has_knowledge_context)

    legacy_answer, legacy_source = ask_qwen_science_assistant(
        question,
        latest,
        conversation_history=conversation_history,
        user_role=user_role,
        model_name=model_name,
        web_context=web_context,
        max_tokens=max_tokens_override,
    )
    return legacy_answer, legacy_source


def build_rule_based_science_answer(
    question: str,
    latest: Optional[SensorReading],
    user_role: str = "student",
) -> str:
    if not latest:
        return "目前还没有实时数据。你可以先采集一次传感器数据，再来问我，我会给你基于数据的科学解释。"

    hints = []
    if latest.temp is not None:
        if latest.temp > 33:
            hints.append("温度偏高，植物蒸腾会加快，可能更容易缺水")
        elif latest.temp < 12:
            hints.append("温度偏低，植物代谢会变慢，生长速度可能下降")
    if latest.soil_moisture is not None:
        if latest.soil_moisture < 20:
            hints.append("土壤湿度偏低，建议观察叶片是否卷曲并及时补水")
        elif latest.soil_moisture > 80:
            hints.append("土壤湿度偏高，可能影响根系透气，注意通风")
    if latest.light is not None and latest.light < 3000:
        hints.append("光照较弱，植物光合作用效率可能不足")

    if not hints:
        hints.append("目前环境参数整体较平稳，可以继续观察并记录变化趋势")

    return f"你的问题是：{question}。结合当前传感器数据，我的建议是：" + "；".join(hints) + "。"


def ask_qwen_science_assistant(
    question: str,
    latest: Optional[SensorReading],
    conversation_history: Optional[list[dict[str, str]]] = None,
    user_role: str = "student",
    model_name: str | None = None,
    web_context: str | None = None,
    max_tokens: int | None = None,
) -> tuple[str, str]:
    api_key = settings.qwen_api_key
    selected_model = model_name or settings.qwen_model
    if not api_key:
        return build_rule_based_science_answer(question, latest, user_role=user_role), SOURCE_RULE_BASED

    telemetry_text = "暂无实时数据"
    if latest:
        telemetry_text = (
            f"温度={float(latest.temp) if latest.temp is not None else '未知'}; "
            f"湿度={float(latest.humidity) if latest.humidity is not None else '未知'}; "
            f"土壤湿度={float(latest.soil_moisture) if latest.soil_moisture is not None else '未知'}; "
            f"光照={float(latest.light) if latest.light is not None else '未知'}"
        )

    messages = [
        {
            "role": "system",
            "content": _science_system_prompt_qwen(user_role),
        }
    ]

    conversation_text = _conversation_to_text(conversation_history)
    if conversation_text:
        messages.append(
            {
                "role": "system",
                "content": f"以下是最近对话，请在回答时保持上下文连续性：\n{conversation_text}",
            }
        )

    messages.append(
        {
            "role": "user",
            "content": (
                f"提问角色：{_science_role_label(user_role)}\n"
                f"问题：{question}\n"
                f"当前大棚数据：{telemetry_text}\n"
                f"联网参考：{web_context or '无'}\n"
                "如果使用了联网参考，请在对应句子末尾标注 [n] 编号（仅使用参考中已有编号）；"
                "若未使用联网参考，请不要添加来源编号。"
            ),
        }
    )

    payload = {
        "model": selected_model,
        "messages": messages,
        "temperature": settings.ai_temperature,
        "max_tokens": max_tokens or settings.ai_max_tokens,
    }

    req = urllib.request.Request(
        url=f"{settings.qwen_base_url.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=settings.ai_timeout_seconds) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        answer = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not answer:
            return build_rule_based_science_answer(question, latest, user_role=user_role), SOURCE_RULE_BASED
        return answer, SOURCE_QWEN
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError):
        return build_rule_based_science_answer(question, latest, user_role=user_role), SOURCE_RULE_BASED


def _safe_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return []


def build_rule_based_assignment_feedback(payload: dict[str, Any]) -> dict[str, Any]:
    observations = str(payload.get("observations") or "").strip()
    conclusion = str(payload.get("conclusion") or "").strip()

    strengths: list[str] = []
    improvements: list[str] = []

    if observations:
        strengths.append("已提供观察记录，具备实验过程意识。")
    else:
        improvements.append("建议补充更具体的实验观察过程（现象、时间、变化趋势）。")

    if conclusion:
        strengths.append("提交了实验结论，具备归纳能力。")
    else:
        improvements.append("建议补充结论并说明结论与观察数据之间的因果关系。")

    if not strengths:
        strengths.append("按时提交了报告，具备基本学习态度。")
    if not improvements:
        improvements.append("可进一步加入图表或分时段数据，提升结论可信度。")

    return {
        "score_band": "75-85",
        "strengths": strengths,
        "improvements": improvements,
        "teacher_comment_draft": "报告完成度较好，建议在观察细节和结论论证上再加强。",
    }


def _clean_outline_line(raw_line: str) -> str:
    line = (raw_line or "").strip()
    if not line:
        return ""

    # Remove prompt-like suffixes such as "请根据以上要点...".
    line = re.split(r"请(?:你)?根据以上", line)[0].strip()
    # Remove long separators like "-----".
    line = re.split(r"[-—_]{3,}", line)[0].strip()
    # Remove bullet and number prefixes.
    line = re.sub(r"^[\-*•\s]+", "", line)
    line = re.sub(r"^\d+\s*[\.、．\)]\s*", "", line)
    line = line.strip("：:;；，,。 ")
    return line


def _extract_outline_points(bullet_points: str) -> list[str]:
    points: list[str] = []
    for raw_line in (bullet_points or "").splitlines():
        cleaned = _clean_outline_line(raw_line)
        if cleaned:
            points.append(cleaned)

    if points:
        return points

    # Fallback: split a long paragraph into sentence-like points.
    chunks = [part.strip() for part in re.split(r"[。；;\n]+", bullet_points or "") if part.strip()]
    for chunk in chunks[:6]:
        cleaned = _clean_outline_line(chunk)
        if cleaned:
            points.append(cleaned)
    return points


def _build_point_paragraph(point: str, tone: str | None = None) -> str:
    tone_hint = tone.strip() if tone else "清晰、课堂友好"
    if "历史" in point:
        return (
            f"同学们，我们先从“{point}”开始。许多科学主题或作物都经历了“发现、传播、改良、应用”的发展过程，"
            "并在不同地区形成了各自的实践经验。理解这段演变历史，能帮助你看到知识如何从实验走向真实生活。"
            f"阅读时请保持{tone_hint}的学习节奏，边看边思考“哪些因素推动了这种变化”。"
        )
    if any(keyword in point for keyword in ["习性", "生长", "环境"]):
        return (
            f"围绕“{point}”，你可以重点关注温度、光照、水分和土壤这四类关键因素。"
            "当某一项指标变化时，植株状态通常会随之改变，例如叶片精神程度、长势快慢和果实品质。"
            "把“环境变化”和“生长结果”对应起来，你就能掌握植物科学观察的核心方法。"
        )
    if any(keyword in point for keyword in ["方法", "种植", "栽培", "步骤"]):
        return (
            f"在“{point}”部分，建议你按“选种育苗-定植管理-水肥调控-病虫害预防-采收复盘”来理解。"
            "每一步都要抓住可操作标准，例如什么时候浇水、什么时候通风、怎么判断是否需要支架。"
            "只要做到“看现象、做记录、再调整”，就能把知识真正变成实践能力。"
        )
    if any(keyword in point for keyword in ["总结", "结语", "归纳"]):
        return (
            "总结时请使用“现象-原因-改进”三步法：先说明你看到了什么，再解释为什么会这样，"
            "最后提出下一步怎么优化。长期坚持这种表达方式，你会更擅长用证据支持自己的结论。"
        )
    return (
        f"围绕“{point}”，你可以按照“提出问题-观察记录-证据讨论-形成结论”的顺序学习。"
        "这个结构能帮助你把零散知识连成完整的科学探究过程。"
    )


def _build_point_activity_paragraph(point: str, tone: str | None = None) -> str:
    tone_hint = tone.strip() if tone else "积极、鼓励"
    return (
        f"实践任务：围绕“{point}”，请你和小组同学先确定 2-3 个观察指标，再分工采集数据。"
        "完成后比较不同小组结果，并解释差异可能来自哪些条件变化。"
        f"交流时保持{tone_hint}表达，尽量用“数据+现象”而不是“我觉得”。"
    )


def _build_point_assessment_paragraph(point: str) -> str:
    return (
        f"自测与表达：学习“{point}”后，尝试用 3 句话完成复盘："
        "我观察到了什么？我如何解释这些现象？下一次我会如何改进？"
        "如果你能做到“结论对应证据”，就说明已经真正掌握了该部分内容。"
    )


def _parse_target_words(target_length: str | None) -> int | None:
    if not target_length:
        return None

    match = re.search(r"(\d{2,5})", target_length.replace(",", ""))
    if not match:
        return None

    return max(200, min(int(match.group(1)), 5000))


def _plain_text_length(value: str | None) -> int:
    if not value:
        return 0

    text = re.sub(r"```[\s\S]*?```", " ", value)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[#>*`_\-]", " ", text)
    text = re.sub(r"\s+", "", text)
    return len(text)


def _looks_teacher_oriented(value: str | None) -> bool:
    text = (value or "").strip()
    if not text:
        return False

    markers = [
        "教师可",
        "建议教师",
        "教学建议",
        "课堂组织建议",
        "授课建议",
        "教师点评",
        "教师可先",
    ]
    return any(marker in text for marker in markers)


def _minimum_polish_length(mode: str, target_length: str | None) -> int:
    target_words = _parse_target_words(target_length)
    if target_words:
        return max(220, int(target_words * 0.65))

    if mode == "article":
        return 1100
    if mode == "expanded":
        return 700
    return 280


def _build_article_from_points(points: list[str], tone: str | None = None, target_length: str | None = None) -> str:
    target_words = _parse_target_words(target_length)
    if target_words and target_words >= 1800:
        paragraphs_per_point = 3
    elif target_words and target_words >= 1000:
        paragraphs_per_point = 2
    else:
        paragraphs_per_point = 1

    intro_topic = "、".join(points[:3]) if points else "科学探究主题"
    sections = []
    for idx, point in enumerate(points, start=1):
        section_blocks = [_build_point_paragraph(point, tone)]
        if paragraphs_per_point >= 2:
            section_blocks.append(_build_point_activity_paragraph(point, tone))
        if paragraphs_per_point >= 3:
            section_blocks.append(_build_point_assessment_paragraph(point))
        sections.append(f"### {idx}. {point}\n" + "\n\n".join(section_blocks))

    return (
        "## 学习目标\n"
        f"本篇学习资源围绕“{intro_topic}”展开。阅读后，你应能解释关键科学现象，"
        "并把观察、记录和改进方法用于真实种植任务。\n\n"
        "## 导入问题\n"
        "为什么在同样的学习主题下，不同小组会得到不同观察结果？"
        "答案通常藏在环境数据、操作细节和记录方法里。\n\n"
        + "\n\n".join(sections)
        + "\n\n## 课堂小结\n"
        "学完本篇内容后，你应能把“环境指标变化”与“植株状态变化”建立对应关系，"
        "并能用证据说明你的判断。科学学习不是记答案，而是学会用数据解释世界。\n\n"
        "## 课后思考\n"
        "1. 如果环境条件持续波动，你预期会出现哪些变化？\n"
        "2. 你会如何调整观察或管理策略来提升结果稳定性？\n"
        "3. 哪项监测数据最能反映当前状态？为什么？"
    )


def build_rule_based_content_polish(
    bullet_points: str,
    mode: str = "conservative",
    tone: str | None = None,
    target_length: str | None = None,
) -> dict[str, Any]:
    points = _extract_outline_points(bullet_points)
    if not points:
        return {
            "title_suggestion": "科学探究小课堂",
            "organized_content": "## 学习目标\n- 请补充教学要点后再生成内容。",
        }

    target_words = _parse_target_words(target_length)

    has_tomato_topic = any("番茄" in point for point in points)
    if has_tomato_topic:
        title = "番茄种植探究：历史、习性与实践"
    else:
        title = f"{points[0][:22]}：教学文章"

    if mode == "conservative":
        body_items = "\n".join([f"- {point}" for point in points])
        content = (
            "## 核心要点\n"
            f"{body_items}\n\n"
            "## 学习引导\n"
            "- 阅读每个要点时，请先说出现象，再解释原因，最后给出改进办法。\n"
            "- 尽量用你记录到的数据支撑判断，避免只凭直觉下结论。\n\n"
            "## 可直接使用的总结句\n"
            "通过本次探究，你不仅掌握了种植步骤，还理解了环境因素如何影响植物生长。"
        )
        if target_words and target_words >= 1000:
            detail_sections = "\n\n".join(
                [
                    f"### {idx}. {point}\n{_build_point_paragraph(point, tone)}"
                    for idx, point in enumerate(points, start=1)
                ]
            )
            content += "\n\n## 详细讲解\n" + detail_sections
        return {
            "title_suggestion": title,
            "organized_content": content,
        }

    # expanded/article both produce complete publish-ready article.
    content = _build_article_from_points(points, tone, target_length=target_length)
    return {
        "title_suggestion": title,
        "organized_content": content,
    }


async def ask_science_assistant(
    question: str,
    latest: Optional[SensorReading],
    conversation_history: Optional[list[dict[str, str]]] = None,
    user_role: str = "student",
    enable_deep_thinking: bool = False,
    enable_web_search: bool = False,
) -> tuple[str, str, dict[str, Any]]:
    return await ask_science_assistant_with_options(
        question=question,
        latest=latest,
        conversation_history=conversation_history,
        user_role=user_role,
        enable_deep_thinking=enable_deep_thinking,
        enable_web_search=enable_web_search,
    )


async def ask_science_assistant_with_options(
    *,
    question: str,
    latest: Optional[SensorReading],
    conversation_history: Optional[list[dict[str, str]]] = None,
    user_role: str = "student",
    enable_deep_thinking: bool = False,
    enable_web_search: bool = False,
    model_name: str | None = None,
) -> tuple[str, str, dict[str, Any]]:
    selected_model = model_name or _resolve_science_model(enable_deep_thinking)
    max_tokens_override = _resolve_science_max_tokens(question, enable_deep_thinking)
    citations: list[dict[str, str]] = []
    web_search_notice: str | None = None
    web_context = ""

    if enable_web_search:
        weather_shortcut = _try_build_weather_answer(question)
        if weather_shortcut:
            weather_answer, weather_citations, weather_notice = weather_shortcut
            return (
                weather_answer,
                SOURCE_WEATHER_API,
                _build_science_response_meta(
                    model_name=selected_model,
                    enable_deep_thinking=enable_deep_thinking,
                    enable_web_search=enable_web_search,
                    citations=weather_citations,
                    web_search_notice=weather_notice,
                ),
            )

        citations, web_search_notice = _search_web_sources(question, max_results=MAX_WEB_SOURCES)
        web_context = _build_web_context(citations)

    knowledge_context, has_knowledge_context = _build_knowledge_context(question)
    answer, source = await _ask_science_assistant_with_context(
        question,
        latest,
        knowledge_context=knowledge_context,
        has_knowledge_context=has_knowledge_context,
        conversation_history=conversation_history,
        user_role=user_role,
        model_name=selected_model,
        web_context=web_context,
        max_tokens_override=max_tokens_override,
    )

    if enable_web_search:
        answer, citations, web_search_notice = align_citations_with_answer(
            answer=answer,
            citations=citations,
            web_search_notice=web_search_notice,
        )
        answer, citations, web_search_notice = _soften_offline_claim_for_weather(
            answer,
            question,
            citations,
            web_search_notice,
        )

    return (
        answer,
        source,
        _build_science_response_meta(
            model_name=selected_model,
            enable_deep_thinking=enable_deep_thinking,
            enable_web_search=enable_web_search,
            citations=citations,
            web_search_notice=web_search_notice,
        ),
    )


async def stream_science_assistant(
    question: str,
    latest: Optional[SensorReading],
    conversation_history: Optional[list[dict[str, str]]] = None,
    user_role: str = "student",
    enable_deep_thinking: bool = False,
    enable_web_search: bool = False,
) -> AsyncIterator[str]:
    async for chunk_dict, _, _ in stream_science_assistant_with_source(
        question,
        latest,
        conversation_history=conversation_history,
        user_role=user_role,
        enable_deep_thinking=enable_deep_thinking,
        enable_web_search=enable_web_search,
    ):
        text = chunk_dict.get("text")
        if text:
            yield text


async def stream_science_assistant_with_source(
    question: str,
    latest: Optional[SensorReading],
    conversation_history: Optional[list[dict[str, str]]] = None,
    user_role: str = "student",
    enable_deep_thinking: bool = False,
    enable_web_search: bool = False,
) -> AsyncIterator[tuple[dict[str, str], str, dict[str, Any]]]:
    async for chunk, source, meta in stream_science_assistant_with_options(
        question=question,
        latest=latest,
        conversation_history=conversation_history,
        user_role=user_role,
        enable_deep_thinking=enable_deep_thinking,
        enable_web_search=enable_web_search,
    ):
        yield chunk, source, meta


async def stream_science_assistant_with_options(
    *,
    question: str,
    latest: Optional[SensorReading],
    conversation_history: Optional[list[dict[str, str]]] = None,
    user_role: str = "student",
    enable_deep_thinking: bool = False,
    enable_web_search: bool = False,
) -> AsyncIterator[tuple[dict[str, str], str, dict[str, Any]]]:
    selected_model = _resolve_science_model(enable_deep_thinking)
    max_tokens_override = _resolve_science_max_tokens(question, enable_deep_thinking)
    citations: list[dict[str, str]] = []
    web_search_notice: str | None = None
    web_context = ""

    if enable_web_search:
        weather_shortcut = _try_build_weather_answer(question)
        if weather_shortcut:
            weather_answer, weather_citations, weather_notice = weather_shortcut
            weather_meta = _build_science_response_meta(
                model_name=selected_model,
                enable_deep_thinking=enable_deep_thinking,
                enable_web_search=enable_web_search,
                citations=weather_citations,
                web_search_notice=weather_notice,
            )
            yield {"text": weather_answer}, SOURCE_WEATHER_API, weather_meta
            return

        citations, web_search_notice = _search_web_sources(question, max_results=MAX_WEB_SOURCES)
        web_context = _build_web_context(citations)

    response_meta = _build_science_response_meta(
        model_name=selected_model,
        enable_deep_thinking=enable_deep_thinking,
        enable_web_search=enable_web_search,
        citations=citations,
        web_search_notice=web_search_notice,
    )

    knowledge_context, has_knowledge_context = _build_knowledge_context(question)
    conversation_context = _conversation_to_text(conversation_history)

    primary_source = _langchain_source(has_knowledge_context)
    emitted = False
    try:
        async for chunk in stream_science_with_langchain(
            question,
            latest,
            knowledge_context=knowledge_context,
            conversation_context=conversation_context,
            web_context=web_context,
            user_role=user_role,
            model_name=selected_model,
            max_tokens=max_tokens_override,
        ):
            emitted = True
            yield chunk, primary_source, response_meta
    except Exception:
        if emitted:
            return

    if emitted:
        return

    answer, fallback_source = await _ask_science_assistant_with_context(
        question,
        latest,
        knowledge_context,
        has_knowledge_context,
        conversation_history=conversation_history,
        user_role=user_role,
        model_name=selected_model,
        web_context=web_context,
        max_tokens_override=max_tokens_override,
    )
    if answer:
        answer, citations, web_search_notice = _soften_offline_claim_for_weather(
            answer,
            question,
            citations,
            web_search_notice,
        )
        response_meta["citations"] = citations
        response_meta["web_search_notice"] = web_search_notice if enable_web_search else None
        response_meta["web_search_used"] = bool(enable_web_search and citations)
        yield {"text": answer}, fallback_source, response_meta


async def generate_assignment_feedback(payload: dict[str, Any]) -> tuple[dict[str, Any], str]:
    ai_result = await generate_assignment_feedback_with_langchain(payload)
    if ai_result:
        return {
            "score_band": str(ai_result.get("score_band") or "75-85"),
            "strengths": _safe_list(ai_result.get("strengths")),
            "improvements": _safe_list(ai_result.get("improvements")),
            "teacher_comment_draft": str(ai_result.get("teacher_comment_draft") or "建议教师结合课堂观察补充评语。"),
        }, SOURCE_LANGCHAIN

    return build_rule_based_assignment_feedback(payload), SOURCE_RULE_BASED


async def polish_teaching_content(
    *,
    bullet_points: str,
    mode: str = "conservative",
    tone: str | None = None,
    target_length: str | None = None,
) -> tuple[dict[str, Any], str]:
    min_length = _minimum_polish_length(mode, target_length)
    ai_result = await polish_teaching_content_with_langchain(
        bullet_points=bullet_points,
        mode=mode,
        tone=tone,
        target_length=target_length,
    )
    if ai_result:
        normalized = {
            "title_suggestion": str(ai_result.get("title_suggestion") or "科学探究小课堂"),
            "organized_content": str(ai_result.get("organized_content") or ""),
        }
        content_text = normalized.get("organized_content") or ""
        is_too_short = _plain_text_length(content_text) < min_length
        teacher_oriented = mode in {"expanded", "article"} and _looks_teacher_oriented(content_text)
        if not is_too_short and not teacher_oriented:
            return normalized, SOURCE_LANGCHAIN

    return (
        build_rule_based_content_polish(
            bullet_points,
            mode=mode,
            tone=tone,
            target_length=target_length,
        ),
        SOURCE_RULE_BASED,
    )
