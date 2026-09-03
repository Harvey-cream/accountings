# 小龙社交记账 — 项目整体架构

> 仓库：`accounting` · 后端 `accountsystem/`（Django）· 前端 `uni_accounting/`（UniApp Vue3）

---

## 1. 系统全景（自上而下）

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           客户端层 (uni_accounting)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  微信小程序 / H5 / App                                                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │ 记账首页  │ │ AI 对话   │ │ 账单报表  │ │ 社区动态  │ │ 个人中心  │        │
│  │ Bill/资产 │ │langchain │ │ Chart    │ │ discover │ │ setting  │        │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘        │
│       │            │            │            │            │                 │
│       └────────────┴────────────┴─────┬──────┴────────────┘                 │
│                                       │  api.js / request.js / langchain_stream.js
└───────────────────────────────────────┼─────────────────────────────────────┘
                                        │ HTTPS  /api/*
┌───────────────────────────────────────┼─────────────────────────────────────┐
│                           接入层 (Nginx + Docker)                            │
├───────────────────────────────────────┼─────────────────────────────────────┤
│  account_nginx :443/80                │                                     │
│    /           → static (H5 构建产物)   │                                     │
│    /api/*      → gunicorn:8899 (WSGI) │                                     │
│    /api/.../chat/stream/  proxy_buffering off (SSE)                         │
└───────────────────────────────────────┼─────────────────────────────────────┘
                                        │
┌───────────────────────────────────────┼─────────────────────────────────────┐
│                      应用层 (Django accountsystem)                           │
├───────────────────────────────────────┼─────────────────────────────────────┤
│  common/          GlobalMiddleware · HttpResult · initia(图标种子)            │
│  config/          settings_debug/pro.yaml · .env · provider                  │
│                                       │                                     │
│  ┌────────────┐ ┌────────────┐ ┌──────┴─────┐ ┌────────────┐               │
│  │ user/      │ │ account/   │ │ comment/   │ │ system/    │               │
│  │ 登录注册    │ │ 记账核心    │ │ 社区社交    │ │ 系统消息    │               │
│  │ JWT·SM2    │ │ 账单·预算   │ │ 帖子评论    │ │ 通知已读    │               │
│  │ OSS 上传   │ │ AI(ai/+svc)│ │ 关注点赞    │ │            │               │
│  └─────┬──────┘ └─────┬──────┘ └──────┬─────┘ └─────┬──────┘               │
│        │              │               │             │                         │
│        └──────────────┴───────────────┴─────────────┘                         │
│                              MySQL (account)                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
┌───────────────────────────────────────┼─────────────────────────────────────┐
│                           外部服务 / 基础设施                                 │
├───────────────────────────────────────┼─────────────────────────────────────┤
│  MySQL 8          Redis              阿里云 OSS          LLM (OpenAI 兼容)    │
│  transaction_*    缓存/会话           头像·帖子图          gpt-agent.cc       │
│  user_*           (可选)             sign_oss_url        DashScope Embedding │
│  langchain_chat                      avatars/posts/      Chroma 向量库 (KB)   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. API 路由总览

```
/api/user/          用户 · 认证 · 积分勋章 · OSS 上传
/api/account/       记账 · 预算 · 资产 · 发票 · LangChain 对话
/api/comment/       社区帖子 · 评论 · 点赞 · 关注
/api/system/        系统消息 · 未读数
```

| 模块 | 代表接口 | 说明 |
|------|----------|------|
| user | `POST login/` `POST info/avatar/` | JWT + SM2；通用 OSS 上传 |
| account | `POST bill/save/` `GET bill/summary/` | 账单 CRUD、统计 |
| account | `GET langchain/chat/` `POST .../stream/` | AI 历史分页；H5 SSE 流式 |
| comment | `POST post/publish/` `POST post/like/` | 动态、互动 |
| system | `GET message/list/` | 站内信 |

---

## 3. Agent 层（福娃鸭 AI · `account/ai/`）

> **分工：** 外层 **LangChain LCEL 管道**（寒暄分支 / 编排）· 内层 **LangGraph 图**（bill / analysis / budget 均为自定义 `StateGraph` Workflow）· 能力经 **finance_tools → services** 访问数据库。  
> 人用 REST（`views` 账单/预算）与 AI 能力链分离；Service 主要供 AI Tool 复用。

### 3.0 目录结构

```
account/
  ai/
    agent/                 # View 入口
      agent.py             # LCEL → orchestrator → to_api_dict / SSE
      func.py              # 寒暄规则匹配
    agents/
      supervisor/          # 调度 Agent
        supervisor_agent.py · supervisor_prompt.py · supervisor_schemas.py
        bill/              # 账单子 Agent（LangGraph Workflow）
          bill_agent.py    # LCEL 外壳 + _graph_to_result
          bill_graph.py    # StateGraph 组装
          bill_nodes.py · bill_router.py · bill_state.py
          bill_prompt.py · bill_schemas.py
        analysis/          # 分析子 Agent（LangGraph Workflow）
          analysis_agent.py · analysis_graph.py · analysis_nodes.py
          analysis_router.py · analysis_state.py · analysis_schemas.py · analysis_prompt.py
        budget/            # 预算子 Agent（规则驱动 Workflow）
          budget_agent.py · budget_graph.py · budget_nodes.py · budget_router.py
          budget_validator.py · budget_state.py · budget_schemas.py · budget_prompt.py
    orchestrator/          # 寒暄短路 → Supervisor → 子 Agent
      state.py · router.py · executor.py · __init__.py · memory.py
    llm/                   # 模型与协议
      llm.py · prompt.py · schemas.py · response.py · llm_utils.py
    tools/
      finance_tools/       # LangChain StructuredTool（AI 侧）
        bill_tools.py      # create/update/query bill
        budget_tools.py
        analysis_tools.py
        common.py          # {success, data, message}
    knowledge/             # 内部财务知识库 RAG（LlamaIndex 仅负责 Knowledge Pipeline）
      data/finance_rules/  # 知识源：budget.md · consumption.md · accounting.md
      ingestion/           # 离线入库：loader → parser → build_index
      index/               # chroma_store.py：Chroma 持久化 + DashScope Embedding 适配
      retriever/           # finance_retriever.py：retrieve_finance_knowledge
      tools/               # knowledge_tools.py：search_finance_knowledge（供 analysis/budget）
      embedding.py · chroma_db/
  services/                # AI 业务能力（碰 ORM）
    expense_service.py
    budget_service.py
    langchain_chat.py      # 对话落库；有 record_id 则不重复建账单
    errors.py
  views.py                 # 人用 API + LangchainChat*（不改契约）
```

### 3.1 分层与调用关系

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Client：langchain.vue → sync POST 或 SSE stream                             │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼─────────────────────────────────────────┐
│  Django View：LangchainChatView / LangchainChatStreamView                    │
│  鉴权 · 存用户消息 · 调 Agent · to_api_dict · 存 AI 消息                      │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │ extract_accounting_info / astream_accounting
┌───────────────────────────────────▼─────────────────────────────────────────┐
│  入口 agent.py：LCEL → orchestrator → to_api_dict / SSE                      │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼─────────────────────────────────────────┐
│  orchestrator：寒暄短路（不进 Supervisor）→ router.decide → executor.execute │
│  Supervisor 判定 task_type → 对应 Agent.run（各自独立 LCEL + 图）            │
│  bill_chain / analysis_chain / budget_chain 互不共用                         │
│  各 Agent 产出 {output, intermediate_steps}                                  │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │ Tool invoke
┌───────────────────────────────────▼─────────────────────────────────────────┐
│  finance_tools（Pydantic Schema + StructuredTool）                           │
│  create_bill / query_bills / analyze_expense / create_budget / ...           │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼─────────────────────────────────────────┐
│  services：expense_service / budget_service → Model/ORM → MySQL              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**框架分工：**

| 层次 | 技术 | 职责 |
|------|------|------|
| 外层入口 | `ai/gateway/agent.py` | 寒暄短路、调 orchestrator、接 API/SSE |
| 调度 | orchestrator + Supervisor | 意图路由到 bill/analysis/budget，不碰业务 |
| 业务管道 | 各 `agents/*/*_agent.py` 自有 LCEL + 图 | 域内构图与 chain，互不共用；bill 为 StateGraph Workflow |
| 工具 | LangChain `StructuredTool` | 参数 Schema、统一 JSON 返回 |
| 业务写读 | Django Service | 唯一建议碰 ORM 的 AI 路径 |
| 人用 API | Django View | 手动记账/预算等，不经 Agent |

### 3.2 单轮对话流（记账）

```
用户: "午饭花了25"
    │
    ▼
_prepare（input / user）
    │
    ▼
orchestrator.run_orchestrator
    │
    ├─ 寒暄 → 短回复（不进 Supervisor）
    │
    ├─ memory：最近 3 轮（更早摘要异步压缩，不阻塞本轮）
    │
    ├─ Supervisor 路由 → task_type=bill
    │
    └─ bill.run（history + 当前句 → Bill Workflow）
           │
           ├─ tool: create_bill → expense_service.create_expense → DB
           │         Observation: {success, data:{id,amount,...}, message}
           │
           ▼
       最终口语回复
    │
    ▼
to_api_dict（带 record_id）
           │
           ▼
       langchain_chat.create_ai_chat_message
           （已有 record_id 则只挂聊天卡片，不二次建账单）
```

### 3.2.1 Bill Workflow（LangGraph StateGraph）

账单域不再用通用 ReAct 外壳，改为业务工作流：改单/删单前强制定位 + 前端确认卡片，避免误改误删。
外层 LCEL 与 `_graph_to_result` 保留；确认场景额外透出 `confirm` 字段供前端渲染。

```
START → context_prepare → intent_router
                              │
        create / query ───────┼──────────────► bill_agent ◄─┐
                              │                   │         │
        update / delete ──► mutation_check        │ tool_calls
                              │   │               ▼         │
                need_confirm ─┘   └─ 已确认 ──► bill_tools ─┘
                              │                   │
                              ▼                   ▼
                       human_confirm ────► result_formatter → END
```

| 节点 | 职责 | 是否调 LLM / Tool |
|------|------|-------------------|
| `context_prepare` | 合并历史与本轮输入；结构化确认由外壳预写入 state | 否 |
| `intent_router` | 结构化输出 `BillIntent`：create/query/update/delete，兜底 query | LLM |
| `mutation_check` | 抽 `BillLocator` 条件 → `search_bills` 定位；0 条报错、1/多条待确认 | LLM + Tool |
| `human_confirm` | 输出确认卡片数据（action + candidates），本轮结束 | 否 |
| `bill_agent` | 按 intent 拼提示词，`bind_tools` 发起 tool_calls | LLM |
| `bill_tools` | `ToolNode` 执行 → finance_tools → Service → DB | Tool |
| `result_formatter` | 统一出参 `{success, message, data}`，messages 留给外层抽 intermediate_steps | 否 |

**确认机制：** `human_confirm` 经 `to_api_dict` 产出 `need_confirm` + `candidates`，落库为 `type=confirm` 卡片。
前端点「确认/取消」时 POST `{confirm: bool, bill_id?, action?}`：取消短路返回；确认强制走 bill，跳过寒暄与 Supervisor。

### 3.2.2 Analysis Workflow（LangGraph StateGraph）

分析域只读汇总，无确认卡。参数归一化映射到现有 Tool（`days` / `category`），不改 Tool/Service。

```
START → context_prepare → intent_router → parameter_normalize
                                              │
                              need_input ─────┼──► END（追问）
                                              │
                                              ▼
                                       analysis_agent
                                              │ tool_calls
                                              ▼
                                       analysis_tools
                                              │
                                              ▼
                                       insight_generate → END
```

意图：`summary` / `category` / `compare`。洞察由 `insight_generate` 把工具 JSON 收成口语，不再依赖 ReAct 末轮自由发挥。

### 3.2.3 Budget Workflow（规则驱动 StateGraph）

预算写操作有层级约束，校验与策略节点用确定性代码（策略经 `query_budget` Tool 探查，不碰 ORM、不让 LLM 判规则）。

```
START → context_prepare → intent_router → parameter_validator
                                              │
                         缺参 need_input ─────┼──► END
                                              ▼
                                        policy_check
                                              │
                         规则失败 ────────────┼──► END
                                              ▼
                                        budget_agent → budget_tools → response_generator → END
```

意图：`set_budget` / `query_budget` / `budget_advice`。金额汇总超限等细规则仍由 Service 最终兜底。

### 3.3 模块职责速查

| 路径 | 职责 |
|------|------|
| `ai/gateway/agent.py` | View 入口：`extract_accounting_info` / `astream_accounting` / `prewarm_runtime` |
| `ai/gateway/func.py` | 寒暄规则匹配 |
| `ai/orchestrator/state.py` | `AgentState`：贯穿调度的统一状态（含 memory_messages） |
| `ai/orchestrator/memory.py` | 最近 3 轮原文；更早对话后台压缩写 cache，热路径不阻塞 |
| `ai/orchestrator/router.py` | `decide`：调 Supervisor 写回 task_type/current_agent |
| `ai/orchestrator/executor.py` | `execute`：按 task_type 调用对应 `Agent.run`，写回结果 |
| `ai/agents/supervisor/supervisor_agent.py` | 调度 Agent：路由，不执行业务 |
| `ai/agents/supervisor/{bill,analysis,budget}/*` | 子 Agent：各域自有管道（`*_agent.py` + `*_prompt.py`）；工具用 `finance_tools` |
| `ai/llm/response.py` | `to_api_dict`：从 create_bill Observation 拼账单卡片字段 |
| `ai/llm/prompt.py` | `REACT_SYSTEM` 等提示词（单 Agent 遗留，业务 prompt 已下沉各 agent） |
| `ai/tools/finance_tools/*` | AI Tools（禁止 Agent 直接调 Service） |
| `ai/knowledge/*` | 内部知识库 RAG：LlamaIndex 建 Chroma 索引；`tools/knowledge_tools.py` 出 `search_finance_knowledge`（禁止 Agent 直接 import llama_index） |
| `services/expense_service.py` 等 | AI 业务能力（create/query/update/analyze…） |
| `services/langchain_chat.py` | 对话消息落库 |
| `views.py` | `LangchainChatView` / `LangchainChatStreamView` |

### 3.4 引入 CrewAI（决策参考，尚未实现）

当前已是 **orchestrator + Supervisor + 三业务 Agent（均为自定义 Workflow）+ 多 Tool** 的 Multi-Agent 骨架。若进一步上 CrewAI，只需在 `orchestrator.executor` 的「协作策略」位替换调度实现，其余不动：

- Crew **只做角色协作/任务路由**，替换 `router.decide` + `executor.execute` 的调度，不写 ORM、不写 View  
- 各 Crew Agent 仍通过 **finance_tools → Service** 碰数据（工具只在 `ai/tools`，Agent 各自 `run` 装配）  
- `AgentState`（user_id/conversation_id/task_type/current_agent/messages/tool_results/final_response）可直接映射 Crew 任务上下文  
- 寒暄短路、SSE 协议、to_api_dict、人用 API **全部保持不动**  

```
View → LCEL(_prepare / 寒暄)
         └─ orchestrator（现: router+executor / 未来: CrewAI 协作层）
                └─ 业务 Agent → finance_tools → services → DB
```

---

## 4. 业务域划分（四大 Django App）

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          account/  记账核心域                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  models: TransactionRecord · Category · Budget · AssetAccount · Invoice     │
│          LangchainChatMessage                                               │
│  views:  账单 list/save/delete · summary · 预算 · 资产 · 发票 · LangChain      │
│  services: langchain_chat (AI 消息落库 + 自动写账单)                          │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                          user/  用户与成长域                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  models: User · UserPointRecord · Medal ...                                   │
│  utils:  jwt_token · sm2 · upload_to_oss · sign_oss_url                     │
│  views:  登录注册 · 签到积分 · 勋章 · 邀请码 · 头像上传                        │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                          comment/  社交域                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  models: UserPost · UserComment · UserPostLike · UserFollow · UserNotice    │
│  views:  发帖(含OSS) · 评论 · 点赞 · 关注 · 动态流                           │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                          system/  系统消息域                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  models: SystemMessage                                                        │
│  views:  消息列表 · 已读 · 未读数                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. 前端架构 (uni_accounting)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         uni_accounting/src                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  config/index.js     API_URL (dev / draccounting.xin)                       │
│  api/api.js          业务 API 封装                                            │
│  api/request.js      JWT · 刷新 · uni.request / uploadFile                   │
│  utils/langchain_stream.js   H5 fetch + SSE 解析                             │
│  store/user.js · theme.js · icon.js                                          │
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │ pages/      │  │ page_       │  │ discover/   │  │ page_       │       │
│  │ login·home  │  │ langchain   │  │ community   │  │ setting     │       │
│  │ chart·bill  │  │ AI 对话页   │  │ publish     │  │ account     │       │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │
│                                                                              │
│  AI 发消息: isLangchainStreamSupported() ? stream : sendLangchainChat 同步    │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         │  build_fronted.sh → accountsystem/static → Nginx /
         ▼
```

---

## 6. 部署拓扑 (Docker Compose)

```
                    Internet
                       │
                       ▼
              ┌────────────────┐
              │  account_nginx │ :80 / :443
              │  SSL + static  │
              └───────┬────────┘
                      │ proxy_pass
              ┌───────▼────────┐
              │  accounting    │ gunicorn WSGI :8899
              │  (mini_app)    │ volume: .:/app
              └───────┬────────┘
          ┌───────────┼───────────┐
          ▼           ▼           ▼
    ┌──────────┐ ┌────────┐ ┌─────────┐
    │ mysql_db │ │redis_db│ │  OSS    │ (外网)
    │  :3306   │ │ :6379  │ │ 阿里云   │
    └──────────┘ └────────┘ └─────────┘
```

| 服务 | 容器名 | 说明 |
|------|--------|------|
| Django | `accounting` | `DJANGO_ENV=production`，入口 `docker-entrypoint.sh` |
| MySQL | `mysql_db` | 持久化卷 `mysql_data` |
| Redis | `redis_db` | 缓存 |
| Nginx | `account_nginx` | 静态 + 反向代理 |

---

## 7. 配置与密钥

| 配置项 | 位置 |
|--------|------|
| 数据库 / Redis | `config/settings_*.yaml` → `settings.py` DATABASES |
| LLM / Embedding | `.env`：`LLM_AGENT_*` · `DASHSCOPE_*` |
| OSS | `settings.py`：`OSS_ACCESS_KEY_*` · `OSS_BUCKET_NAME` |
| 环境切换 | `DJANGO_ENV`：debug / production |

---

## 8. 数据流小结

```
记账（手动）:  前端 → POST /api/account/bill/save/ → View → ORM → TransactionRecord
记账（AI）:    前端 → /langchain/chat(/stream/)
                 → LCEL → Bill Workflow(StateGraph) → create_bill Tool
                 → expense_service → TransactionRecord
                 → langchain_chat 挂卡片（record_id）
查账（AI）:    analyze_expense / query_bills Tool → expense_service → 口语化回复
预算（AI）:    create_budget / query_budget Tool → budget_service
社交:          uploadFile(OSS) → publish post → comment DB
用户:          SM2 登录 → JWT → 各 API Authorization Header
```

---

*文档随代码结构更新。Agent 实现以 `account/ai/`、`account/services/` 与 `account/views.py` 为准。*
