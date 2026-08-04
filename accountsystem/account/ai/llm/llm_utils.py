"""LLM 响应解析等通用工具。"""

import traceback


def log_agent_exc(tag: str, exc: BaseException, **context) -> None:
    """打印 Agent 异常：类型、repr、可选上下文、完整堆栈。"""
    ctx = " ".join(f"{k}={v!r}" for k, v in context.items())
    head = f"[{tag}] {type(exc).__name__}: {exc!r}"
    if ctx:
        head += f" | {ctx}"
    print(head)
    print(traceback.format_exc())


def extract_content(reply) -> str:
    content = getattr(reply, "content", None)
    if content is None:
        return str(reply).replace("\n", " ").replace("\r", " ").strip()
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("text"):
                parts.append(str(item["text"]))
        return " ".join(parts).replace("\n", " ").replace("\r", " ").strip()
    return str(content).replace("\n", " ").replace("\r", " ").strip()


def json_from_text(text: str) -> str:
    t = (text or "").strip()
    start, end = t.find("{"), t.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("no JSON in model output")
    return t[start : end + 1]

