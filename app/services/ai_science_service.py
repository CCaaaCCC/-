import json
import os
import urllib.error
import urllib.request
from typing import Optional

from app.db.models import SensorReading


def build_rule_based_science_answer(question: str, latest: Optional[SensorReading]) -> str:
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

    return f"你的问题是：{question}。结合当前大棚数据，我的结论是：" + "；".join(hints) + "。"


def ask_qwen_science_assistant(question: str, latest: Optional[SensorReading]) -> tuple[str, str]:
    api_key = os.getenv("QWEN_API_KEY", "").strip()
    model_name = os.getenv("QWEN_MODEL", "qwen-plus")
    if not api_key:
        return build_rule_based_science_answer(question, latest), "rule-based"

    telemetry_text = "暂无实时数据"
    if latest:
        telemetry_text = (
            f"温度={float(latest.temp) if latest.temp is not None else '未知'}; "
            f"湿度={float(latest.humidity) if latest.humidity is not None else '未知'}; "
            f"土壤湿度={float(latest.soil_moisture) if latest.soil_moisture is not None else '未知'}; "
            f"光照={float(latest.light) if latest.light is not None else '未知'}"
        )

    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是中小学科学课的智慧大棚助手。"
                    "请用孩子能听懂的话回答，先解释现象，再给1-2条可执行建议，"
                    "语气鼓励，避免术语堆砌，回答控制在120字以内。"
                ),
            },
            {
                "role": "user",
                "content": f"学生问题：{question}\n当前大棚数据：{telemetry_text}",
            },
        ],
        "temperature": 0.4,
    }

    req = urllib.request.Request(
        url="https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        answer = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not answer:
            return build_rule_based_science_answer(question, latest), "rule-based"
        return answer, "qwen"
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError):
        return build_rule_based_science_answer(question, latest), "rule-based"
