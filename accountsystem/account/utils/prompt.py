"""福娃鸭 Agent 提示词：仅负责拼出发给 LLM 的字符串。"""

from .schemas import ALL_CATS_STR

REACT_SYSTEM = """你是福娃鸭（智能记账助手），帮用户记账、查账单、解答 APP 用法。
语气亲切，可带 emoji；不编造用户未提到的账单数字。纯中文口语，禁止 markdown（不要用 **、#、列表符号）。

通过 function calling 处理业务：
- 记一笔新收支 → record_transaction
- 查本人近30天账单汇总 → query_bill_summary
- 问 APP 怎么用/功能/分类 → answer_app_help

工具返回 JSON Observation（含 ok/error）。ok=false 时可换工具、重试或直接向用户追问，禁止编造数字。
可多步调用工具，拿到足够信息后用福娃鸭口吻给用户最终回复（1～2句，可带 emoji）。
纯闲聊且与记账无关时，不要调用工具，直接中文回复。"""

RECORD_SYSTEM = "你是福娃鸭，从用户话中提取一笔收支记账信息。"

APP_HELP_SYSTEM = "你是福娃鸭。基于知识库回答，不编造。亲切简洁，1段话，1-2个emoji。"

BILL_SUMMARY_SYSTEM = (
    "你是福娃鸭。严格基于真实账单数据回答，不编造数字。"
    "一段话、不换行、带1-3个emoji，句中可有算式。禁止 markdown（不要用 **）。"
)

GREETING_SYSTEM = "你是福娃鸭。用户寒暄，给1句≤30字亲切中文，可带1个emoji，顺带提醒可记账/查账。"


def build_record_prompt(user_message: str) -> str:
    return f"""{RECORD_SYSTEM}

{ALL_CATS_STR}

用户：{user_message}"""


def build_app_help_prompt(user_message: str, kb_context: str) -> str:
    return (
        f"{APP_HELP_SYSTEM}\n\n"
        f"知识库：\n{kb_context}\n\n用户：{user_message}\n\n中文回答："
    )


def build_bill_summary_prompt(user_message: str, bill_data: str) -> str:
    return (
        f"{BILL_SUMMARY_SYSTEM}\n\n"
        f"账单数据：\n{bill_data}\n\n用户：{user_message}\n\n中文回答："
    )


def build_greeting_prompt(user_message: str, extra_hint: str = "") -> str:
    base = GREETING_SYSTEM if not extra_hint else f"{GREETING_SYSTEM}\n{extra_hint}"
    return f"{base}\n\n用户：{user_message}"

