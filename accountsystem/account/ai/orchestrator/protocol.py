"""Structured protocol shared by the unified multi-agent planner."""

# ============================================================
# 承载状态的"数据结构"（Pydantic 模型）
# ============================================================
# | 模型                | 作用                                   | 关键字段                                          |
# |---------------------|----------------------------------------|--------------------------------------------------|
# | StepError           | 错误对象                               | code/message/details                             |
# | ConfirmationRequest | 确认请求                               | prompt/token/payload                             |
# | StepResult          | 步骤执行结果（最关键）                 | status/success/data/confirmation/error/intermediate_steps |
# | StepStatus          | 步骤状态                               | pending/running/waiting_*/completed/failed/...   |
# | StepType            | 步骤业务域                             | bill/budget/asset/invoice/open_planning/chat     |
# ============================================================

from __future__ import annotations

from enum import Enum
from typing import TypeAlias

# Python 3.10 compatibility for StrEnum
class StrEnum(str, Enum):
    pass

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.types import JsonValue

JsonObject: TypeAlias = dict[str, JsonValue]


class StepStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING_CONFIRMATION = "waiting_confirmation"
    WAITING_INPUT = "waiting_input"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class StepType(StrEnum):
    BILL = "bill"
    BUDGET = "budget"
    ASSET = "asset"
    INVOICE = "invoice"
    OPEN_PLANNING = "open_planning"
    CHAT = "chat"


class ProtocolModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class StepError(ProtocolModel):
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    details: JsonObject = Field(default_factory=dict)


class ConfirmationRequest(ProtocolModel):
    prompt: str = Field(min_length=1)
    token: str | None = None
    payload: JsonObject = Field(default_factory=dict)


class StepResult(ProtocolModel):
    plan_id: str = Field(min_length=1)
    step_id: str = Field(min_length=1)
    step_type: StepType
    action: str = Field(min_length=1)
    status: StepStatus
    success: bool
    data: JsonObject = Field(default_factory=dict)
    entity_ids: list[int] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    error: StepError | None = None
    confirmation: ConfirmationRequest | None = None
    message: str = ""
    summary: str = ""
    intermediate_steps: list[JsonValue] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_status(self) -> "StepResult":
        if self.status == StepStatus.COMPLETED and not self.success:
            raise ValueError("completed step results must be successful")
        if self.status == StepStatus.FAILED and self.success:
            raise ValueError("failed step results cannot be successful")
        if self.status == StepStatus.WAITING_CONFIRMATION and self.confirmation is None:
            raise ValueError("waiting confirmation results require confirmation details")
        return self
