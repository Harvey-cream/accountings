from dataclasses import dataclass

from langchain_core.documents import Document

from .embedding import build_embeddings
from .vector_chroma import build_chroma_from_documents


@dataclass(frozen=True)
class SkillSpec:
    name: str
    when: str
    output_schema: str
    prototypes: tuple[str, ...]
    tool: str


SKILLS: tuple[SkillSpec, ...] = (
    SkillSpec(
        name="knowledge_qa",
        when=(
            "仅产品/操作/规则说明。关键词：怎么、如何、功能、支持、有什么分类、教程、步骤、什么是。"
            "不统计真实账单数字，不新增记账。"
        ),
        output_schema="知识点 -> 关键步骤 -> 注意事项",
        prototypes=(
            "怎么在APP里手动记账？",
            "餐饮和零食分类怎么区分？",
            "福娃鸭能做什么功能？",
        ),
        tool="knowledge_rag",
    ),
    SkillSpec(
        name="bill_stats",
        when=(
            "查账/汇总类：看历史、算总额、要对比/趋势/报表；用户在对「已有账单」做提问。"
            "典型说法含：多少(疑问句)、花多少/收入多少(问数)、共、汇总、总、近30天、本月、"
            "报表、收支、结余、各分类。注意：与「要记下本次一笔新账」不同。"
        ),
        output_schema="统计周期 -> 收支总览 -> 关键结论",
        prototypes=(
            "我这个月一共花了多少？",
            "最近30天收入支出各多少？",
            "看账单汇总和各分类排名",
        ),
        tool="query_stats",
    ),
    SkillSpec(
        name="record_parser",
        when=(
            "记一笔/新增交易：把当前这句话当成「要落库的一单」。"
            "典型：具体金额(元/块)、刚发生、刚刚/今天、买了/花了/充了/到账/工资/红包/收了一笔。"
            "不是查旧账：没有「共多少/汇总/统计/报表/这月花了多少(疑问)」等仅查询语气。"
        ),
        output_schema="type/category/money/account/remark/reply",
        prototypes=(
            "刚刚奶茶花了15元",
            "午饭花了25块钱",
            "今天工资到账5000",
            "帮我记 地铁充值100",
        ),
        tool="record_extract",
    ),
    SkillSpec(
        name="learning_planner",
        when="求职学习路线、冲刺计划、项目补齐",
        output_schema="目标拆分 -> 周任务 -> 里程碑 -> 复盘",
        prototypes=(
            "用户要制定面试准备计划、冲刺节奏和里程碑。",
            "用户希望拆解周任务并给出复盘节奏。",
        ),
        # 当前系统无独立 learning_planner 工具，先路由到知识问答工具。
        tool="knowledge_rag",
    ),
)

SKILL_DOCS = [
    Document(
        page_content=(
            f"[技能:{s.name}][工具:{s.tool}] 适用场景: {s.when} 输出: {s.output_schema} "
            f"例句: {' | '.join(s.prototypes)}"
        ),
        metadata={"tool": s.tool, "skill": s.name},
    )
    for s in SKILLS
]

ALL_TOOL_NAMES = sorted({s.tool for s in SKILLS})
_skill_vector_store = None


def _get_skill_vector_store():
    global _skill_vector_store
    if _skill_vector_store is None:
        embeddings = build_embeddings()
        # 文案变化后需用新 collection，否则会沿用磁盘里旧 embedding。
        _skill_vector_store = build_chroma_from_documents(
            "account_skills_routing_v3", SKILL_DOCS, embeddings
        )
    return _skill_vector_store


def prewarm_skill_store():
    """启动预热 skill 向量索引。"""
    _get_skill_vector_store()
    print("[SKILL_PREWARM] skill vector store ready")


def _fallback_record_skill() -> SkillSpec:
    for s in SKILLS:
        if s.name == "record_parser":
            return s
    return SKILLS[0]


def match_best_skill(user_input: str) -> tuple[SkillSpec, float]:
    """
    向量相似度只取 Top1 技能（1 个 skill -> 1 个默认 tool 提示）。
    无结果或异常时回退为 record_parser，避免主链断裂。
    """
    try:
        store = _get_skill_vector_store()
        pairs = store.similarity_search_with_score(user_input, k=1)
        if not pairs:
            return _fallback_record_skill(), 0.0
        d, distance = pairs[0]
        skill_name = d.metadata.get("skill")
        for s in SKILLS:
            if s.name == skill_name:
                return s, float(distance)
    except Exception as e:
        print(f"[SKILL_MATCH] failed: {e}")
    return _fallback_record_skill(), 0.0


def match_tools_by_skill(user_input: str, top_k: int = 2):
    """
    基于向量匹配返回推荐工具列表（按相似度高到低、互不重复）。

    若 k 取太小，命中可能两条属于同一技能，去重后只剩 1 个工具，后 ReAct 无法二选一纠偏。
    因此多取若干条再按顺序去重，不是业务规则，只是向量召回的结构修复。
    若异常则回退为全工具。
    """
    try:
        store = _get_skill_vector_store()
        fetch_k = max(top_k * 5, 10)
        pairs = store.similarity_search_with_score(user_input, k=fetch_k)
        scored = []
        for d, score in pairs:
            tool = d.metadata.get("tool")
            skill = d.metadata.get("skill", "")
            if tool in ALL_TOOL_NAMES:
                scored.append((tool, str(skill), float(score)))
        print(f"[SKILL_ROUTE] top={scored[:6]}")
        names = []
        for tool, _skill, _s in scored:
            if tool not in names:
                names.append(tool)
            if len(names) >= top_k:
                break
        if names:
            print(f"[SKILL_ROUTE] tools={names}")
            return names
    except Exception as e:
        print(f"[SKILL_ROUTE] failed: {e}")
    return list(ALL_TOOL_NAMES)
