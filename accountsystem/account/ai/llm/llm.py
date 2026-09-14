from langchain_openai import ChatOpenAI

from account.ai.llm.failover import FailoverLLM
from config.dotenv_loader import env_str

LLM_AGENT_BASE_URL = env_str("LLM_AGENT_BASE_URL", "https://api4.mygptlife.com/v1/")
LLM_AGENT_API_KEY = env_str("LLM_AGENT_API_KEY")
LLM_AGENT_MODEL = env_str("LLM_AGENT_MODEL", "claude-sonnet-4-6")
AGENT_MAX_ITERATIONS = int(env_str("AGENT_MAX_ITERATIONS", "4"))

# 分层模型：主模型负责业务与规划，simple(luna) 负责分类/摘要脏活。
# 两档共用同一 OpenAI 兼容端点，仅模型名不同；未配置时回退主模型。
LLM_MODEL_SIMPLE = env_str("LLM_MODEL_SIMPLE", LLM_AGENT_MODEL)


def _split_models(raw: str) -> list[str]:
    """解析逗号分隔的模型列表，去空、去重、保序。"""
    out: list[str] = []
    for name in (raw or "").split(","):
        name = name.strip()
        if name and name not in out:
            out.append(name)
    return out


# 兜底链：主模型失败时按顺序顺延。此列表放**全部候选模型**（含主模型），
# 拼接链时会把与主模型重名的那一项去掉——因此只改 LLM_AGENT_MODEL 就能整体换序：
#   主 claude → claude -> gpt-5.6-luna -> gemini-3.7-flash
#   主 luna   → luna   -> claude-sonnet-4-6 -> gemini-3.7-flash
LLM_AGENT_FALLBACK_MODELS: list[str] = _split_models(
    env_str("LLM_AGENT_FALLBACK_MODELS", "claude-sonnet-4-6,gpt-5.6-luna,gemini-3.7-flash")
)


def _model_chain(primary: str) -> list[str]:
    """主模型 + 其余候选模型，去重保序（与主模型重名的那项跳过）。"""
    return [primary] + [m for m in LLM_AGENT_FALLBACK_MODELS if m != primary]


# 任务类型 -> 模型档位。open_planning 和固定业务走主模型，其余分类/摘要走 simple。
MODEL_ROUTER = {
    "open_planning": LLM_AGENT_MODEL,
    "bill": LLM_AGENT_MODEL,
    "asset": LLM_AGENT_MODEL,
    "invoice": LLM_AGENT_MODEL,
    "budget": LLM_AGENT_MODEL,
    "simple": LLM_MODEL_SIMPLE,
    "default": LLM_AGENT_MODEL,
}

if not LLM_AGENT_API_KEY:
    print(
        "[WARN] LLM_AGENT_API_KEY 未设置，请在 accountsystem/.env 中配置（可复制 .env.example）"
    )


def build_llm(
    model_name: str = LLM_AGENT_MODEL,
    *,
    request_timeout: float = 30,
    max_retries: int = 2,
) -> FailoverLLM:
    """构建主模型 + 兜底的顺序链；单模型失败自动顺延，全部失败才抛出最后一个异常。"""
    models = [
        ChatOpenAI(
            model_name=name,
            openai_api_base=LLM_AGENT_BASE_URL,
            openai_api_key=LLM_AGENT_API_KEY,
            request_timeout=request_timeout,
            max_retries=max_retries,
            temperature=0.2,
        )
        for name in _model_chain(model_name)
    ]
    return FailoverLLM(models)


_llm_cache: dict[str, FailoverLLM] = {}


def get_llm(tier: str = "default") -> FailoverLLM:
    """按任务档位取 LLM 实例（进程内缓存）。tier 未知时回退 default。"""
    model_name = MODEL_ROUTER.get(tier, MODEL_ROUTER["default"])
    if model_name not in _llm_cache:
        _llm_cache[model_name] = build_llm(model_name)
    return _llm_cache[model_name]


llm = build_llm()

# Planner 专用实例：放宽超时、关闭 SDK 自动重试（应用层自行控制最多一次 schema retry）。
# 其余 LLM 保持各自现有配置，不受影响。
PLANNER_TIMEOUT = float(env_str("PLANNER_LLM_TIMEOUT", "45"))
planner_llm = build_llm(LLM_AGENT_MODEL, request_timeout=PLANNER_TIMEOUT, max_retries=0)

print(f"[LLM] chain = {' -> '.join(llm.model_names)}")
