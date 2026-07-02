from langchain_openai import ChatOpenAI

from config.dotenv_loader import env_str

LLM_AGENT_BASE_URL = env_str("LLM_AGENT_BASE_URL", "https://gpt-agent.cc/v1")
LLM_AGENT_API_KEY = env_str("LLM_AGENT_API_KEY")
LLM_AGENT_MODEL = env_str("LLM_AGENT_MODEL", "gpt-5.4")
AGENT_MAX_ITERATIONS = int(env_str("AGENT_MAX_ITERATIONS", "4"))

if not LLM_AGENT_API_KEY:
    print(
        "[WARN] LLM_AGENT_API_KEY 未设置，请在 accountsystem/.env 中配置（可复制 .env.example）"
    )


def build_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model_name=LLM_AGENT_MODEL,
        openai_api_base=LLM_AGENT_BASE_URL,
        openai_api_key=LLM_AGENT_API_KEY,
        request_timeout=30,
        temperature=0.2,
    )


llm = build_llm()
