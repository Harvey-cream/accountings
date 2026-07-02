from .schemas import (
    DEFAULT_CHAT_REPLY,
    AccountingResult,
    ToolObservation,
    accounting_response,
    chat_response,
)


def _parse_observation(raw: str) -> ToolObservation | None:
    try:
        return ToolObservation.model_validate_json(raw)
    except Exception:
        return None


def _last_record(steps) -> AccountingResult | None:
    record = None
    for _action, observation in steps:
        obs = _parse_observation(observation)
        if obs and obs.ok and obs.kind == "record" and obs.record:
            record = obs.record
    return record


def to_api_dict(agent_result: dict) -> dict:
    steps = agent_result.get("intermediate_steps") or []
    output = (agent_result.get("output") or "").strip()

    record = _last_record(steps)
    if record:
        reply = output or record.reply or f"已记下{record.category}{record.money:g}元～"
        return accounting_response(record.model_copy(update={"reply": reply}))

    return chat_response(output or DEFAULT_CHAT_REPLY)


def chat(reply: str) -> dict:
    return chat_response(reply)
