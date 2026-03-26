import os
import json
from langchain_community.llms import Tongyi
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.tools import Tool
from langchain.agents import create_react_agent, AgentExecutor
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from .icons import NORMAL_ICONS
from datetime import date, timedelta
from account.models import TransactionRecord
from django.db.models import Sum


# 加载环境变量
load_dotenv()

# 通义千问 API Key
API_KEY = os.getenv("DASHSCOPE_API_KEY", "sk-042f623078aa47ffbd19ee3466da2638")
os.environ["DASHSCOPE_API_KEY"] = API_KEY

# 从 icons.py 提取所有合法的分类名称，用于约束 AI 输出
EXPENSE_CATS = list(set([icon['name'] for icon in NORMAL_ICONS if icon['type'] in ('expense', 'all')]))
INCOME_CATS = list(set([icon['name'] for icon in NORMAL_ICONS if icon['type'] in ('income', 'all')]))
ALL_CATS_STR = "支出分类包括: " + "/".join(EXPENSE_CATS) + "\n收入分类包括: " + "/".join(INCOME_CATS)

# 创建 LLM
llm = Tongyi(
    model="qwen-turbo",
    dashscope_api_key=API_KEY,
    temperature=0.2
)

# 定义 Pydantic 模型作为输出结构
class AccountingResult(BaseModel):
    type: str = Field(description="支出/收入")
    category: str = Field(description=f"账单分类。如果是支出，必须从以下选择: {EXPENSE_CATS}。如果是收入，必须从以下选择: {INCOME_CATS}")
    money: float = Field(description="金额数字，如 15.00")
    account: str = Field(description="支付账户，如 微信/支付宝/现金/银行卡，如果不确定则填'其他'")
    remark: str = Field(description="备注信息")
    reply: str = Field(description="一句幽默、亲切且符合'福娃鸭'身份的回复语，确认记账成功")

# 结构化解析器
output_parser = JsonOutputParser(pydantic_object=AccountingResult)
format_instructions = output_parser.get_format_instructions()

# 提示词模板（记账用）
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
# ===== 向量 RAG 知识库（业务说明） =====
KB_DOCS = [
    Document(page_content="怎么手动记账：打开APP→点击底部‘记账’→选择收入或支出→填写金额、分类、备注→保存即可。", metadata={"title": "怎么手动记账"}),
    Document(page_content="怎么用AI对话记账：在聊天框输入一句话，例如‘喝奶茶花了15元’，AI会自动识别并记账。", metadata={"title": "怎么用AI对话记账"}),
    Document(page_content="分类说明：支出分类有餐饮、购物、交通、娱乐、医疗、教育、住房、通讯、零食、其他；收入分类有工资、奖金、兼职、理财、红包、退款、其他。", metadata={"title": "分类说明"}),
    Document(page_content="软件功能：支持AI记账、手动记账、账单统计、账单查询、预算管理。", metadata={"title": "功能介绍"}),
    Document(page_content="福娃鸭人设：可爱、亲切、幽默，会用emoji，会鼓励用户好好记账。", metadata={"title": "福娃鸭人设"}),
]

_kb_vector_store = None

def _get_kb_vector_store():
    global _kb_vector_store
    if _kb_vector_store is None:
        embeddings = DashScopeEmbeddings(
            model="text-embedding-v2",
            dashscope_api_key=API_KEY,
        )
        _kb_vector_store = FAISS.from_documents(KB_DOCS, embeddings)
    return _kb_vector_store

def _retrieve_kb_context(text: str, top_k: int = 2) -> str:
    """向量检索：按语义相似度返回最相关知识片段"""
    try:
        store = _get_kb_vector_store()
        docs = store.similarity_search(text, k=top_k)
        if not docs:
            return ""
        return "\n".join([d.page_content for d in docs])
    except Exception as e:
        print(f"知识库向量检索失败: {e}")
        return ""

def _fmt_amount(v):
    """金额格式化：3000.00 -> 3000，3000.50 -> 3000.5"""
    try:
        n = float(v)
        if n.is_integer():
            return str(int(n))
        return ("%s" % n).rstrip('0').rstrip('.')
    except Exception:
        return str(v)


def _format_formula(amounts):
    """把金额列表转成 200 + 300 + 500 这种算式字符串"""
    if not amounts:
        return ""
    return " + ".join([_fmt_amount(a) for a in amounts])


def _get_last_month_summary(user) -> str:
    """
    查询用户最近一个月的收支数据，返回拼接好的文字供 AI 参考。
    包含：笔数、总额、算式明细。
    """
    try:
        today = date.today()
        start = today - timedelta(days=30)
        records = TransactionRecord.objects.filter(
            user=user,
            date__gte=start,
            date__lte=today
        ).select_related('category')

        if not records.exists():
            return "最近一个月暂无账单记录。"

        expense_qs = records.filter(type='expense').order_by('date', 'time', 'id')
        income_qs = records.filter(type='income').order_by('date', 'time', 'id')

        # 总收支
        total_expense = expense_qs.aggregate(s=Sum('amount'))['s'] or 0
        total_income = income_qs.aggregate(s=Sum('amount'))['s'] or 0

        # 金额列表（最多展示前20笔，避免 prompt 太长）
        income_amounts = list(income_qs.values_list('amount', flat=True)[:20])
        expense_amounts = list(expense_qs.values_list('amount', flat=True)[:20])

        income_formula = _format_formula(income_amounts)
        expense_formula = _format_formula(expense_amounts)

        # 按分类汇总支出（给 AI 更多上下文）
        cat_stats = (
            expense_qs
            .values('category__name')
            .annotate(total=Sum('amount'))
            .order_by('-total')
        )
        cat_lines = [f"  {s['category__name']}: {_fmt_amount(s['total'])}元" for s in cat_stats]

        lines = [
            f"统计周期：{start} 至 {today}",
            f"收入笔数：{income_qs.count()}笔",
            f"支出笔数：{expense_qs.count()}笔",
            f"总收入：{_fmt_amount(total_income)}元",
            f"总支出：{_fmt_amount(total_expense)}元",
            f"净结余：{_fmt_amount(total_income - total_expense)}元",
            f"收入算式：{income_formula if income_formula else '无收入记录'} = {_fmt_amount(total_income)}",
            f"支出算式：{expense_formula if expense_formula else '无支出记录'} = {_fmt_amount(total_expense)}",
        ]
        if cat_lines:
            lines.append("各分类支出：")
            lines.extend(cat_lines)

        return "\n".join(lines)
    except Exception as e:
        print(f"查询账单失败: {e}")
        return "账单数据查询失败，请稍后再试。"


def _tool_knowledge_rag(user_input: str) -> str:
    """Tool1: 向量 RAG 知识检索 + 回答"""
    kb_context = _retrieve_kb_context(user_input)
    if not kb_context:
        kb_context = "怎么手动记账：打开APP→点击底部‘记账’→选择收入或支出→填写金额、分类、备注→保存即可。"
    kb_prompt = (
        "你是记账助手福娃鸭，请基于下方知识库内容回答用户问题，不要编造。"
        "语气亲切、简洁，1段话，带1-2个emoji即可。\n\n"
        f"知识库内容：\n{kb_context}\n\n"
        f"用户问题：{user_input}\n\n"
        "请用中文回答："
    )
    reply = llm.invoke(kb_prompt)
    return str(reply).replace("\n", " ").replace("\r", " ").strip()


def _tool_query_stats(user_input: str, user=None) -> str:
    """Tool2: 账单查询统计 + 生活化回复"""
    if user is None:
        return "当前无法查询账单，因为缺少用户信息。"
    summary = _get_last_month_summary(user)
    prompt = (
        "你是记账助手福娃鸭，语气生活化、接地气、像朋友聊天。"
        "请严格基于下方真实账单数据回答，不要编造数字。"
        "输出要求：只输出一段话，不要换行，不要分点，不要标题，必须带1-3个emoji。"
        "句子里自然带上算式（例如 200+300+500=1000）和结论，语气暖一点。\n\n"
        f"账单数据：\n{summary}\n\n"
        f"用户问题：{user_input}\n\n"
        "请用中文回答："
    )
    reply = llm.invoke(prompt)
    reply = str(reply).replace("\n", " ").replace("\r", " ")
    while "  " in reply:
        reply = reply.replace("  ", " ")
    return reply.strip()


def _tool_record_extract(user_input: str) -> str:
    """Tool3: 记账结构化提取"""
    _input = prompt_template.format_prompt(text=user_input)
    output = llm.invoke(_input.to_string())
    parsed_output = output_parser.parse(output)
    return json.dumps(parsed_output, ensure_ascii=False)


def _run_agent(user_input: str, user=None) -> dict:
    """ReAct Agent：自动路由到 3 个工具（强约束版）"""
    tools = [
        Tool(
            name="knowledge_rag",
            func=_tool_knowledge_rag,
            description=(
                "仅用于【产品知识问答】。适用：怎么用/功能介绍/分类说明/操作步骤。"
                "不适用：收支统计查询、记一笔账。"
                "输入：用户原话。输出：一段中文解释。"
            )
        ),
        Tool(
            name="query_stats",
            func=lambda q: _tool_query_stats(q, user=user),
            description=(
                "仅用于【账单统计查询】。适用：本月花了多少、近30天收入支出、收支汇总。"
                "不适用：教程说明、记一笔账。"
                "输入：用户原话。输出：一段包含数字结论的中文。"
            )
        ),
        Tool(
            name="record_extract",
            func=_tool_record_extract,
            description=(
                "仅用于【记账信息提取】。适用：用户要记一笔（如：奶茶15、工资3000）。"
                "不适用：教程说明、统计查询。"
                "输入：用户原话。输出：JSON字符串，包含type/category/money/account/remark/reply。"
            )
        ),
    ]

    react_prompt = PromptTemplate.from_template(
        "你是记账助手的路由Agent。你必须在以下两种模式中二选一：\n"
        "模式1：直接回复（不调用工具）——用于寒暄/闲聊（如 在吗、你好）。\n"
        "模式2：调用且仅调用1次工具——用于知识问答、统计查询、记账提取。\n\n"
        "工具列表：\n{tools}\n\n"
        "可选工具名：{tool_names}\n\n"
        "硬性规则：\n"
        "1) 最多只允许一次 Action，禁止二次及以上 Action。\n"
        "2) 若是寒暄闲聊，直接给 Final Answer，不要调用工具。\n"
        "3) 若调用工具，Action 必须是 {tool_names} 之一，Action Input 用用户原话。\n"
        "4) 最终必须输出 Final Answer，且只输出中文一段话；若工具返回JSON则直接原样作为 Final Answer。\n\n"
        "严格按以下格式输出：\n"
        "Question: 用户问题\n"
        "Thought: 你的简短思考\n"
        "Action: 工具名（仅在需要时）\n"
        "Action Input: 输入（仅在需要时）\n"
        "Observation: 工具结果（仅在调用后）\n"
        "Thought: 我已得到最终答案\n"
        "Final Answer: 最终答案\n\n"
        "Question: {input}\n"
        "Thought:{agent_scratchpad}"
    )

    agent = create_react_agent(llm=llm, tools=tools, prompt=react_prompt)
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,
        handle_parsing_errors=True,
        max_iterations=2,
        max_execution_time=10,
    )

    router_prompt = (
        "请先判断是否是寒暄。若是寒暄直接回复。若不是寒暄，按规则只调用1次最合适工具。\n"
        f"用户输入：{user_input}"
    )

    result = executor.invoke({"input": router_prompt})
    result_text = str(result.get("output", "")).strip()

    # 统一返回格式，兼容原 views.py
    if result_text.startswith("{") and '"money"' in result_text:
        try:
            return json.loads(result_text)
        except Exception:
            pass

    if (
        not result_text
        or "Agent stopped due to iteration limit or time limit" in result_text
        or "iteration limit" in result_text.lower()
    ):
        result_text = "我在呀～你可以直接说“刚刚午饭花了25”或“我这个月花了多少”"

    return {
        "type": "支出",
        "category": "其他",
        "money": 0.0,
        "account": "其他",
        "remark": "",
        "reply": result_text
    }


def extract_accounting_info(text, user=None):
    """主入口：交给 ReAct Agent 自动选择 Tool"""
    try:
        return _run_agent(text, user=user)
    except Exception as e:
        print(f"Agent 执行失败: {str(e)}")
        return {
            "type": "支出",
            "category": "其他",
            "money": 0.0,
            "account": "其他",
            "remark": text,
            "reply": "哎呀，鸭鸭刚才走神了，没听清呢。您可以再说一遍吗？比如：'买奶茶花了15元'~"
        }
