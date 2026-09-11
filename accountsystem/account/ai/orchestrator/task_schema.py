"""Strong schemas for the planner-to-executor workflow contract."""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator

WorkflowType = Literal["bill", "budget", "asset", "invoice", "open_planning", "chat"]

BillAction = Literal["create", "batch_create", "query", "update", "delete"]
BudgetAction = Literal["set_budget", "query_budget", "budget_advice"]
AssetAction = Literal["create", "query", "update", "delete", "adjust_balance"]
InvoiceAction = Literal["create", "query", "update", "delete"]
OpenPlanningAction = Literal["analyze"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BillItem(StrictModel):
    amount: float = Field(gt=0)
    category: str = "其他"
    date: str | None = None
    description: str = ""
    bill_type: str = "expense"


class BillCreateInput(BillItem):
    pass


class BillBatchCreateInput(StrictModel):
    items: list[BillItem] = Field(min_length=1)


class BillQueryInput(StrictModel):
    keyword: str | None = None
    category: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    days: int | None = Field(default=30, ge=1, le=365)
    bill_type: str | None = None
    limit: int = Field(default=20, ge=1, le=100)


class BillUpdateInput(StrictModel):
    bill_id: int | None = None
    keyword: str | None = None
    category: str | None = None
    date: str | None = None
    days: int | None = Field(default=30, ge=1, le=365)
    bill_type: str | None = None
    amount: float | None = Field(default=None, gt=0)
    new_category: str | None = None
    description: str | None = None
    new_bill_type: str | None = None

    @model_validator(mode="after")
    def validate_update(self):
        if self.bill_id is None and not any((self.keyword, self.category, self.date)):
            raise ValueError("bill update requires bill_id or locator fields")
        if all(
            getattr(self, name) is None
            for name in ("amount", "new_category", "description", "new_bill_type")
        ):
            raise ValueError("bill update requires at least one changed field")
        return self


class BillDeleteInput(StrictModel):
    bill_id: int | None = None
    keyword: str | None = None
    category: str | None = None
    date: str | None = None
    days: int | None = Field(default=30, ge=1, le=365)
    bill_type: str | None = None

    @model_validator(mode="after")
    def validate_target(self):
        if self.bill_id is None and not any((self.keyword, self.category, self.date)):
            raise ValueError("bill delete requires bill_id or locator fields")
        return self


class BudgetInput(StrictModel):
    amount: float | None = Field(default=None, ge=0)
    period: str | None = None
    budget_type: Literal["month", "year"] | None = None
    is_total: bool = True
    category: str | None = None

    @model_validator(mode="after")
    def validate_budget(self):
        if self.amount is None:
            raise ValueError("budget set requires amount")
        if not self.period:
            raise ValueError("budget set requires period")
        if not self.budget_type:
            raise ValueError("budget set requires budget_type")
        if not self.is_total and not self.category:
            raise ValueError("category budget requires category")
        return self


class BudgetQueryInput(StrictModel):
    period: str
    budget_type: Literal["month", "year"] = "month"


class AssetCreateInput(StrictModel):
    name: str = Field(min_length=1)
    asset_type: str = Field(min_length=1)
    balance: float = 0
    account_type: Literal["asset", "debt"] | None = None
    is_included_in_total: bool = True
    remark: str = ""


class AssetQueryInput(StrictModel):
    account_id: int | None = None
    name: str | None = None


class AssetUpdateInput(StrictModel):
    account_id: int
    name: str | None = None
    asset_type: str | None = None
    balance: float | None = None
    account_type: Literal["asset", "debt"] | None = None
    is_included_in_total: bool | None = None
    remark: str | None = None

    @model_validator(mode="after")
    def has_update(self):
        if all(
            getattr(self, name) is None
            for name in (
                "name",
                "asset_type",
                "balance",
                "account_type",
                "is_included_in_total",
                "remark",
            )
        ):
            raise ValueError("asset update requires at least one changed field")
        return self


class AssetDeleteInput(StrictModel):
    account_id: int


class AssetAdjustBalanceInput(StrictModel):
    account_id: int
    delta: float


class InvoiceCreateInput(StrictModel):
    name: str = Field(min_length=1)
    tax_id: str = Field(min_length=1)
    amount: float = 0
    address: str = ""
    phone: str = ""
    bank: str = ""
    account: str = ""
    remark: str = ""


class InvoiceQueryInput(StrictModel):
    invoice_id: int | None = None
    keyword: str | None = None


class InvoiceUpdateInput(StrictModel):
    invoice_id: int
    name: str | None = None
    tax_id: str | None = None
    amount: float | None = None
    address: str | None = None
    phone: str | None = None
    bank: str | None = None
    account: str | None = None
    remark: str | None = None

    @model_validator(mode="after")
    def has_update(self):
        if all(getattr(self, name) is None for name in ("name", "tax_id", "amount", "address", "phone", "bank", "account", "remark")):
            raise ValueError("invoice update requires at least one changed field")
        return self


class InvoiceDeleteInput(StrictModel):
    invoice_id: int


class OpenPlanningInput(StrictModel):
    topic: str = Field(min_length=1)


class ChatRespondInput(StrictModel):
    message: str = Field(min_length=1, description="用户本轮要说的话")


TaskInput = Annotated[
    Union[
        BillCreateInput,
        BillBatchCreateInput,
        BillQueryInput,
        BillUpdateInput,
        BillDeleteInput,
        BudgetInput,
        BudgetQueryInput,
        AssetCreateInput,
        AssetQueryInput,
        AssetUpdateInput,
        AssetDeleteInput,
        AssetAdjustBalanceInput,
        InvoiceCreateInput,
        InvoiceQueryInput,
        InvoiceUpdateInput,
        InvoiceDeleteInput,
        OpenPlanningInput,
        ChatRespondInput,
    ],
    Field(discriminator=None),
]

_ACTION_INPUTS = {
    ("bill", "create"): BillCreateInput,
    ("bill", "batch_create"): BillBatchCreateInput,
    ("bill", "query"): BillQueryInput,
    ("bill", "update"): BillUpdateInput,
    ("bill", "delete"): BillDeleteInput,
    ("budget", "set_budget"): BudgetInput,
    ("budget", "query_budget"): BudgetQueryInput,
    ("budget", "budget_advice"): BudgetQueryInput,
    ("asset", "create"): AssetCreateInput,
    ("asset", "query"): AssetQueryInput,
    ("asset", "update"): AssetUpdateInput,
    ("asset", "delete"): AssetDeleteInput,
    ("asset", "adjust_balance"): AssetAdjustBalanceInput,
    ("invoice", "create"): InvoiceCreateInput,
    ("invoice", "query"): InvoiceQueryInput,
    ("invoice", "update"): InvoiceUpdateInput,
    ("invoice", "delete"): InvoiceDeleteInput,
    ("open_planning", "analyze"): OpenPlanningInput,
    ("chat", "respond"): ChatRespondInput,
}


class WorkflowTask(BaseModel):
    id: str = Field(min_length=1)
    type: WorkflowType
    action: str = Field(min_length=1)
    goal: str = ""
    input: dict = Field(description="Action-specific validated input")
    depends_on: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def validate_action_input(cls, value):
        if not isinstance(value, dict):
            return value
        task_type = value.get("type")
        action = value.get("action")
        if not task_type:
            raise ValueError("task type is required")
        if not action:
            raise ValueError("task action is required")
        input_value = value.get("input")
        if input_value is None:
            raise ValueError("task input is required")
        input_model = _ACTION_INPUTS.get((task_type, action))
        if input_model is None:
            raise ValueError(f"unsupported action {action!r} for task type {task_type!r}")
        value = dict(value)
        value["input"] = input_model.model_validate(input_value).model_dump(mode="json")
        return value

    @property
    def input_model(self) -> StrictModel:
        return _ACTION_INPUTS[(self.type, self.action)].model_validate(self.input)


class WorkflowPlan(BaseModel):
    tasks: list[WorkflowTask] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_dependencies(self):
        ids = [task.id for task in self.tasks]
        if len(set(ids)) != len(ids):
            raise ValueError("task ids must be unique")
        known = set(ids)
        for task in self.tasks:
            if len(set(task.depends_on)) != len(task.depends_on):
                raise ValueError(f"task {task.id!r} dependencies must be unique")
            if task.id in task.depends_on:
                raise ValueError(f"task {task.id!r} cannot depend on itself")
            unknown = set(task.depends_on) - known
            if unknown:
                raise ValueError(f"task {task.id!r} depends on unknown tasks: {sorted(unknown)}")
        return self


def topo_sort(plan: WorkflowPlan) -> list[WorkflowTask] | None:
    remaining = {task.id: set(task.depends_on) for task in plan.tasks}
    ordered: list[WorkflowTask] = []
    while remaining:
        ready = [task for task in plan.tasks if task.id in remaining and not remaining[task.id]]
        if not ready:
            return None
        for task in ready:
            ordered.append(task)
            del remaining[task.id]
            for dependencies in remaining.values():
                dependencies.discard(task.id)
    return ordered
