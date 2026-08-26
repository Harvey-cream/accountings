"""Structured protocol shared by the unified multi-agent planner."""

from __future__ import annotations

from enum import Enum, StrEnum
from typing import TypeAlias

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.types import JsonValue

JsonPrimitive: TypeAlias = str | int | float | bool | None
JsonObject: TypeAlias = dict[str, JsonValue]


class PlanStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING_CONFIRMATION = "waiting_confirmation"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


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


class ProtocolModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PlanStep(ProtocolModel):
    step_id: str = Field(min_length=1)
    step_type: StepType
    action: str = Field(min_length=1)
    goal: str = ""
    input: JsonObject = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)
    status: StepStatus = StepStatus.PENDING

    @model_validator(mode="after")
    def validate_dependencies(self) -> "PlanStep":
        if self.step_id in self.depends_on:
            raise ValueError("a step cannot depend on itself")
        if len(set(self.depends_on)) != len(self.depends_on):
            raise ValueError("step dependencies must be unique")
        return self


class Plan(ProtocolModel):
    plan_id: str = Field(min_length=1)
    version: int = Field(default=1, ge=1)
    original_request: str = ""
    status: PlanStatus = PlanStatus.PENDING
    steps: list[PlanStep] = Field(min_length=1)
    metadata: JsonObject = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_steps(self) -> "Plan":
        step_ids = [step.step_id for step in self.steps]
        if len(set(step_ids)) != len(step_ids):
            raise ValueError("plan step ids must be unique")
        known_ids = set(step_ids)
        for step in self.steps:
            unknown = set(step.depends_on) - known_ids
            if unknown:
                raise ValueError(
                    f"step {step.step_id!r} depends on unknown steps: {sorted(unknown)}"
                )
        return self


class StepContext(ProtocolModel):
    plan_id: str = Field(min_length=1)
    step_id: str = Field(min_length=1)
    step_type: StepType
    input: JsonObject = Field(default_factory=dict)
    planning_request: str = ""
    completed_results: dict[str, "StepResult"] = Field(default_factory=dict)
    metadata: JsonObject = Field(default_factory=dict)


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


StepContext.model_rebuild()
