import json

from langchain_core.prompts import PromptTemplate
from langchain_core.tools import Tool


def _extract_content(reply) -> str:
    """统一提取模型返回正文，只保留 content。"""
    content = getattr(reply, "content", None)
    if content is None:
        return str(reply).replace("\n", " ").replace("\r", " ").strip()
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                txt = item.get("text")
                if txt:
                    parts.append(str(txt))
        return " ".join(parts).replace("\n", " ").replace("\r", " ").strip()
    return str(content).replace("\n", " ").replace("\r", " ").strip()


def tool_knowledge_rag(user_input: str, llm, retrieve_kb_context, llm_model: str, llm_base_url: str) -> str:
    """Tool1: 向量 RAG 知识检索 + 回答"""
    print("[EMBEDDING_STAGE] start retrieve kb context")
    kb_context = retrieve_kb_context(user_input)
    if not kb_context:
        kb_context = "怎么手动记账：打开APP→点击底部‘记账’→选择收入或支出→填写金额、分类、备注→保存即可。"
    kb_prompt = (
        "你是记账助手福娃鸭，请基于下方知识库内容回答用户问题，不要编造。"
        "语气亲切、简洁，1段话，带1-2个emoji即可。\n\n"
        f"知识库内容：\n{kb_context}\n\n"
        f"用户问题：{user_input}\n\n"
        "请用中文回答："
    )
    print(f"[LLM_START] tool=knowledge_rag model={llm_model} base={llm_base_url}")
    reply = llm.invoke(kb_prompt)
    return _extract_content(reply)


def tool_query_stats(user_input: str, user, llm, get_last_month_summary, llm_model: str, llm_base_url: str) -> str:
    """Tool2: 账单查询统计 + 生活化回复"""
    if user is None:
        return "当前无法查询账单，因为缺少用户信息。"
    summary = get_last_month_summary(user)
    prompt = (
        "你是记账助手福娃鸭，语气生活化、接地气、像朋友聊天。"
        "请严格基于下方真实账单数据回答，不要编造数字。"
        "输出要求：只输出一段话，不要换行，不要分点，不要标题，必须带1-3个emoji。"
        "句子里自然带上算式（例如 200+300+500=1000）和结论，语气暖一点。\n\n"
        f"账单数据：\n{summary}\n\n"
        f"用户问题：{user_input}\n\n"
        "请用中文回答："
    )
    print(f"[LLM_START] tool=query_stats model={llm_model} base={llm_base_url}")
    reply = llm.invoke(prompt)
    reply = _extract_content(reply)
    while "  " in reply:
        reply = reply.replace("  ", " ")
    return reply.strip()


def tool_record_extract(user_input: str, llm, prompt_template, output_parser, llm_model: str, llm_base_url: str) -> str:
    """Tool3: 记账结构化提取"""
    _input = prompt_template.format_prompt(text=user_input)
    print(f"[LLM_START] tool=record_extract model={llm_model} base={llm_base_url}")
    output = llm.invoke(_input.to_string())
    # JsonOutputParser.parse 要 str；invoke 返回 AIMessage，会触发 Generation.text 校验错误
    text_out = _extract_content(output)
    parsed_output = output_parser.parse(text_out)
    return json.dumps(parsed_output, ensure_ascii=False)


def tool_greeting_polish(
    user_input: str,
    llm,
    llm_model: str,
    llm_base_url: str,
    extra_system_hint: str = "",
) -> str:
    """寒暄润色：由大模型生成更自然回复。"""
    base = (
        "你是记账助手福娃鸭。用户在寒暄，请给出1句简短、亲切、自然的中文回复。"
        "要求：不超过30字，可带1个emoji，并顺带提醒可直接说记账或统计需求。"
    )
    if extra_system_hint:
        base = f"{base}\n补充说明：{extra_system_hint}"
    prompt = f"{base}\n\n用户输入：{user_input}"
    print(f"[LLM_START] tool=greeting_polish model={llm_model} base={llm_base_url}")
    reply = llm.invoke(prompt)
    text = _extract_content(reply)
    return text or "我在呀～你可以直接说“刚刚午饭花了25”或“我这个月花了多少”"


def build_react_tools(
    user,
    llm,
    retrieve_kb_context,
    get_last_month_summary,
    prompt_template,
    output_parser,
    llm_model: str,
    llm_base_url: str,
    allowed_tool_names=None,
):
    tools = [
        Tool(
            name="knowledge_rag",
            func=lambda q: tool_knowledge_rag(q, llm, retrieve_kb_context, llm_model, llm_base_url),
            description=(
                "【产品/操作知识】仅当用户在问「怎么用、有什么功能、分类规则、步骤说明」，"
                "且没有要求查自己真实账单汇总、也没有说「记一笔具体金额」。"
                "输入：用户原话。输出：一段中文解释。"
            ),
        ),
        Tool(
            name="query_stats",
            func=lambda q: tool_query_stats(q, user, llm, get_last_month_summary, llm_model, llm_base_url),
            description=(
                "【查历史账单汇总】用户想知道自己花/赚了多少、收支对比、近30天或本月统计、各分类合计、"
                "带「多少」「汇总」「统计」「报表」「一共」等查询语气。与「刚发生的小额消费要记入账本」不同。"
                "输入：用户原话。输出：带真实数据结论的中文一段话。"
            ),
        ),
        Tool(
            name="record_extract",
            func=lambda q: tool_record_extract(q, llm, prompt_template, output_parser, llm_model, llm_base_url),
            description=(
                "【记这一笔账】用户要新增一条收支：句子里有具体金额、或明确说记一笔/帮记，"
                "如「刚花了25块」「咖啡18元」「今天工资5000到了」。"
                "不是问「我总共/本月花了多少」这种查表问题。"
                "输入：用户原话。输出：JSON 字符串(type/category/money/account/remark/reply)。"
            ),
        ),
    ]
    if not allowed_tool_names:
        return tools
    by_name = {t.name: t for t in tools}
    # 与 skill 向量匹配顺序一致，相关度高的工具排在 tools 串前，利于 ReAct 选对
    filtered = [by_name[n] for n in allowed_tool_names if n in by_name]
    return filtered or tools


def get_react_prompt():
    return PromptTemplate.from_template(
        "你是记账助手的路由Agent。必须调用且仅调用1次工具；当前输入已非寒暄，不要省略工具、直接当闲聊来答。\n\n"
        "分流（结合工具说明优先判断，禁止混淆）：\n"
        "— 用户要「把这句话记成一笔有金额的账」、陈述刚发生的消费/收入（含元/块/数字+花/买/到账等） → record_extract。\n"
        "— 用户要「查自己已有账单的多少、总额、近30天、本月汇总、分类合计」、疑问语气问花多少/收入多少 → query_stats。\n"
        "— 用户只问产品怎么用、功能、操作步骤、分类怎么选、教程 → knowledge_rag。\n"
        "若 {tool_names} 里只出现了其中一部分工具名，你必须在这几个里选，不要选未列出的名。\n\n"
        "工具列表：\n{tools}\n\n"
        "当前允许的工具名：{tool_names}\n\n"
        "硬性规则：\n"
        "1) 必须且只能有一次 Action。\n"
        "2) Action 必须精确等于 {tool_names} 中的某一个；Action Input 用用户原话（可整句原样复制）。\n"
        "3) 最终必须输出 Final Answer：若工具返回为 JSON 字符串，则 Final Answer 与 Observation 中 JSON 文本完全一致、一字不改；否则为工具返回自然语言全文。\n\n"
        "严格按以下格式输出：\n"
        "Question: 用户问题\n"
        "Thought: 你的简短思考\n"
        "Action: 工具名\n"
        "Action Input: 输入\n"
        "Observation: 工具结果\n"
        "Thought: 我已得到最终答案\n"
        "Final Answer: 最终答案\n\n"
        "Question: {input}\n"
        "Thought:{agent_scratchpad}"
    )
