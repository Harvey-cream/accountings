import os
import json
import dashscope
from langchain_community.llms import Tongyi
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from .icons import NORMAL_ICONS

# 加载环境变量
load_dotenv()

# 通义千问 API Key
API_KEY = os.getenv("DASHSCOPE_API_KEY", "sk-042f623078aa47ffbd19ee3466da2638")
dashscope.api_key = API_KEY

# 1. 从 icons.py 提取所有合法的分类名称，用于约束 AI 输出
EXPENSE_CATS = list(set([icon['name'] for icon in NORMAL_ICONS if icon['type'] == 'expense' or icon['type'] == 'all']))
INCOME_CATS = list(set([icon['name'] for icon in NORMAL_ICONS if icon['type'] == 'income' or icon['type'] == 'all']))
ALL_CATS_STR = "支出分类包括: " + "/".join(EXPENSE_CATS) + "\n收入分类包括: " + "/".join(INCOME_CATS)

# 1. 创建 LLM
llm = Tongyi(
    model="qwen-turbo",
    dashscope_api_key=API_KEY,
    temperature=0.1
)

# 2. 定义 Pydantic 模型作为输出结构
class AccountingResult(BaseModel):
    type: str = Field(description="支出/收入")
    category: str = Field(description=f"账单分类。如果是支出，必须从以下选择: {EXPENSE_CATS}。如果是收入，必须从以下选择: {INCOME_CATS}")
    money: float = Field(description="金额数字，如 15.00")
    account: str = Field(description="支付账户，如 微信/支付宝/现金/银行卡，如果不确定则填'其他'")
    remark: str = Field(description="备注信息")
    reply: str = Field(description="一句幽默、亲切且符合'福娃鸭'身份的回复语，确认记账成功")

# 3. 结构化解析器
output_parser = JsonOutputParser(pydantic_object=AccountingResult)
format_instructions = output_parser.get_format_instructions()

# 4. 提示词模板
prompt_template = PromptTemplate(
    template="""
你是专业的智能记账助手“福娃鸭”，性格幽默、亲切。
请根据用户输入的文本提取记账信息。

必须严格遵守以下分类规则：
{all_categories}

{format_instructions}

用户输入：{text}
""",
    input_variables=["text"],
    partial_variables={
        "format_instructions": format_instructions,
        "all_categories": ALL_CATS_STR
    }
)

def extract_accounting_info(text):
    """
    调用 LangChain 提取记账信息
    """
    try:
        # 构建并调用
        _input = prompt_template.format_prompt(text=text)
        output = llm.invoke(_input.to_string())
        
        # 解析结果
        parsed_output = output_parser.parse(output)
        return parsed_output
    except Exception as e:
        print(f"LangChain 提取失败: {str(e)}")
        # 兜底返回
        return {
            "type": "支出",
            "category": "其他",
            "money": 0.0,
            "account": "其他",
            "remark": text,
            "reply": "哎呀，鸭鸭刚才走神了，没听清呢。您可以再说一遍吗？比如：'买奶茶花了15元'~ 🦆"
        }
