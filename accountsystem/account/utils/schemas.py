"""Pydantic 模型：约束路由决策与各工具返回数据。"""

from typing import Literal

from common.initia import NORMAL_ICONS
from pydantic import BaseModel, Field, field_validator, model_validator

EXPENSE_CATS = list(
    {icon["name"] for icon in NORMAL_ICONS if icon["type"] in ("expense", "all")}
)
INCOME_CATS = list(
    {icon["name"] for icon in NORMAL_ICONS if icon["type"] in ("income", "all")}
)
ALL_CATS_STR = (
    f"支出分类: {'/'.join(EXPENSE_CATS)}\n收入分类: {'/'.join(INCOME_CATS)}"
)

DEFAULT_CHAT_REPLY = "我在呀～你可以直接说「刚刚午饭25」或「这月花多少」~"

APP_HELP_EMPTY_REPLY = "可以在聊天框直接说「奶茶15元」让我帮你记账哦～"
BILL_SUMMARY_EMPTY_REPLY = "暂时没查到账单数据，稍后再试试吧～"
BILL_SUMMARY_NO_USER = "当前无法查询账单，因为缺少用户信息。"
AGENT_ERROR_REPLY = "哎呀，鸭鸭刚才走神了，没听清呢。您可以再说一遍吗？比如：'买奶茶花了15元'~"


class TextReply(BaseModel):
    reply: str = Field(
        min_length=1,
        description="福娃鸭口吻的1～2句互动语，须贴合工具结果中的金额或统计，可爱有趣",
    )



class AccountingResult(BaseModel):
    type: Literal["支出", "收入"] = "支出"
    category: str = "其他"
    money: float = Field(ge=0, description="金额")
    account: str = "其他"
    remark: str = ""
    reply: str = ""

    @field_validator("type", mode="before")
    @classmethod
    def normalize_type(cls, v):
        return v if v in ("支出", "收入") else "支出"

    @model_validator(mode="after")
    def normalize_fields(self):
        allowed = EXPENSE_CATS if self.type == "支出" else INCOME_CATS
        if self.category not in allowed:
            object.__setattr__(self, "category", "其他")
        acct = (self.account or "其他").strip() or "其他"
        if acct not in ("微信", "支付宝", "现金", "银行卡", "其他"):
            acct = "其他"
        object.__setattr__(self, "account", acct)
        return self


class ToolObservation(BaseModel):
    ok: bool
    kind: Literal["record", "text"]
    record: AccountingResult | None = None
    text: str = ""
    error: str | None = None

    def for_agent(self) -> str:
        return self.model_dump_json(ensure_ascii=False)


def chat_response(reply: str) -> dict:
    text = TextReply(reply=(reply or DEFAULT_CHAT_REPLY).strip()).reply
    return {
        "type": "支出",
        "category": "其他",
        "money": 0.0,
        "account": "其他",
        "remark": "",
        "reply": text,
    }


def accounting_response(result: AccountingResult) -> dict:
    return result.model_dump()
