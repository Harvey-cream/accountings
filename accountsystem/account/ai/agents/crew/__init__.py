"""CrewAI 开放式任务协作层。

只处理"开放式规划任务"（年度消费规划 / 综合财务分析 / 消费优化 / 财富规划报告），
不替代 Bill/Analysis/Budget 三个 LangGraph Workflow，也不直接访问数据库：
Crew Agent -> LangChain Tool -> Service -> DB。

crewai 为可选依赖：本包顶层不导入 crewai，缺失时开放任务优雅降级，不影响固定业务链路。
"""
