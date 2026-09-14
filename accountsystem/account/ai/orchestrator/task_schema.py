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
    # extra="forbid"：Planner 幻觉出未知业务字段时必须报错重试，而不是静默丢弃。
    # reason 是唯一的例外——Planner 习惯在 input 里附带一句说明，容忍它，避免整条
    # 复合计划因为一句解释性文字而整体失败。exclude=True：接收但不出现在任何
    # model_dump / 确认卡载荷里。
    model_config = ConfigDict(extra="forbid")

    reason: str | None = Field(default=None, exclude=True)


class BillItem(StrictModel):
    amount: float = Field(gt=0)
    category: str = "其他"
    date: str | None = None
    description: str = ""
    bill_type: str = "expense"


class BillCreateInput(BillItem):
    # 单笔记账允许缺金额：不是 schema 错误，而是"意图明确、参数不全"，
    # 由 Bill Workflow 的 AMOUNT_REQUIRED 守卫停下追问（WAITING_INPUT）。
    # 批量 items 仍强制 amount，避免半截草稿混进批量落库。
    amount: float | None = Field(default=None, gt=0)


class BillBatchCreateInput(StrictModel):
    items: list[BillItem] = Field(min_length=1)


class BillQueryInput(StrictModel):
    keyword: str | None = None
    category: str | None = None
    exclude_category: str | None = None
    period: str | None = None
    date: str | None = None
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
    # amount/period/budget_type 全部可选：缺参不是 schema 错误，交给 Budget Workflow
    # 的 validate_budget_params 停下追问（WAITING_INPUT），而不是让 Planner 输出失败。
    amount: float | None = Field(default=None, ge=0)
    period: str | None = None
    budget_type: Literal["month", "year"] | None = None
    is_total: bool = True
    category: str | None = None


class BudgetQueryInput(StrictModel):
    period: str | None = None
    budget_type: Literal["month", "year"] = "month"


class AssetCreateInput(StrictModel):
    # 缺 name/asset_type 交给 Asset Workflow 的 DRAFT_INCOMPLETE 追问
    name: str | None = None
    asset_type: str | None = None
    balance: float = 0
    account_type: Literal["asset", "debt"] | None = None
    is_included_in_total: bool = True
    remark: str = ""


class AssetQueryInput(StrictModel):
    account_id: int | None = None
    name: str | None = None


class AssetUpdateInput(StrictModel):
    """改账户：account_id 与 keyword 至少给一个（用户通常只说账户名）。

    name/asset_type/balance… 是"要改成什么"，keyword 才是"改哪一个"，两者不可混用。
    """

    account_id: int | None = None
    keyword: str | None = None
    name: str | None = None
    asset_type: str | None = None
    balance: float | None = None
    account_type: Literal["asset", "debt"] | None = None
    is_included_in_total: bool | None = None
    remark: str | None = None

    @model_validator(mode="after")
    def has_update(self):
        if self.account_id is None and not (self.keyword or "").strip():
            raise ValueError("asset update requires account_id or keyword locator")
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
    account_id: int | None = None
    keyword: str | None = None

    @model_validator(mode="after")
    def validate_target(self):
        if self.account_id is None and not (self.keyword or "").strip():
            raise ValueError("asset delete requires account_id or keyword locator")
        return self


class AssetAdjustBalanceInput(StrictModel):
    account_id: int | None = None
    keyword: str | None = None
    delta: float

    @model_validator(mode="after")
    def validate_target(self):
        if self.account_id is None and not (self.keyword or "").strip():
            raise ValueError("asset adjust requires account_id or keyword locator")
        return self


class InvoiceCreateInput(StrictModel):
    # 缺抬头/税号交给 Invoice Workflow 的 NAME_TAXID_REQUIRED 追问
    name: str | None = None
    tax_id: str | None = None
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
    """改发票：invoice_id 与 keyword 至少给一个（用户通常只说抬头名）。"""

    invoice_id: int | None = None
    keyword: str | None = None
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
        if self.invoice_id is None and not (self.keyword or "").strip():
            raise ValueError("invoice update requires invoice_id or keyword locator")
        if all(getattr(self, name) is None for name in ("name", "tax_id", "amount", "address", "phone", "bank", "account", "remark")):
            raise ValueError("invoice update requires at least one changed field")
        return self


class InvoiceDeleteInput(StrictModel):
    invoice_id: int | None = None
    keyword: str | None = None

    @model_validator(mode="after")
    def validate_target(self):
        if self.invoice_id is None and not (self.keyword or "").strip():
            raise ValueError("invoice delete requires invoice_id or keyword locator")
        return self


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

    @model_validator(mode="before")
    @classmethod
    def normalize_task_ids(cls, value):
        """Planner 漏写 id（或写成数字）时补全，避免整条计划因一个标识符失败。

        只填空缺，不动 Planner 已给出的 id——depends_on 引用的都是它自己写的 id，
        因此补全不会破坏依赖关系；新建 id 也避开已用集合，不制造重复。
        同时把 id / depends_on 统一成字符串：Planner 用数字下标命名时，
        "1" 与 1 混用会让依赖校验误判成未知任务。
        """
        if not isinstance(value, dict):
            return value
        tasks = value.get("tasks")
        if not isinstance(tasks, list):
            return value

        def _sid(raw) -> str:
            return "" if raw is None else str(raw).strip()

        used = {_sid(task.get("id")) for task in tasks if isinstance(task, dict) and _sid(task.get("id"))}
        normalized: list = []
        counter = 0
        for task in tasks:
            if not isinstance(task, dict):
                normalized.append(task)
                continue
            raw = _sid(task.get("id"))
            if not raw:
                while True:
                    counter += 1
                    candidate = f"task_{counter}"
                    if candidate not in used:
                        break
                used.add(candidate)
                raw = candidate
            item = {**task, "id": raw}
            if "depends_on" in item:
                item["depends_on"] = [
                    _sid(dep) for dep in (item.get("depends_on") or []) if _sid(dep)
                ]
            normalized.append(item)
        return {**value, "tasks": normalized}

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
