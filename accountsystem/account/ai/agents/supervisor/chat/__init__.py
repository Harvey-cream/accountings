"""Chat Agent：普通聊天 + 财务知识问答。对外只暴露 run（供 orchestrator.executor 调用）。"""

from .chat_agent import run

__all__ = ["run"]
