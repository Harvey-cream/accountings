# 记账本 (Accounting)

面向个人用户的一站式智能财务管理平台，覆盖日常记账、账单统计、预算、资产、发票、财务分析与社区互动，并结合自然语言交互、RAG、记忆与 Agent Workflow，提供智能记账、财务问答和个性化财务分析能力。AI 助手「福娃鸭」是平台内的智能交互与任务执行层，而非产品本身。

## 功能特性

### 💰 财务管理
- 收入 / 支出记账，多分类账单（支持分类与图标管理）
- 账单查询、按日期 / 类型筛选、编辑与删除
- 收支统计与趋势：总览、月度 / 年度汇总、分类排行、趋势图
- 预算管理：年总 / 月总 / 分类多层级预算，实时追踪使用进度并做超支约束
- 资产账户：资产 / 负债账户、余额与净值汇总、余额调整
- 发票管理：抬头、税号、金额等信息的维护

### 🤖 AI 财务助手（福娃鸭）
- 自然语言记账：单笔与批量，自动解析金额、分类、日期
- 自然语言查账：账单 / 预算 / 资产 / 发票的查询与统计
- 自然语言财务操作：修改账单、调整预算、创建资产、维护发票等
- 财务知识问答：基于内部知识库的 RAG 检索
- 财务分析与规划：CrewAI 多角色协作产出结构化分析报告
- 多轮对话记忆：Chat Memory 提供连续对话上下文
- Human-in-the-loop：写操作支持参数校验、目标定位与确认卡片
- H5 SSE 流式：实时执行状态与逐字回复

### 👥 社区与社交
- 发布动态（图文）
- 点赞
- 评论互动
- 关注
- 消息通知

### 👤 用户与成长体系
- JWT 认证登录
- SM2 国密加密
- 用户资料与头像上传（阿里云 OSS）
- 每日签到
- 积分奖励
- 勋章成就
- 邀请二维码
- 个性化主题（多套配色）

## 技术栈

### 后端
- Python 3.12
- Django + Django REST Framework
- MySQL 8 / Redis 7
- LangChain（LCEL / Tools）+ LangGraph（领域 Workflow）
- CrewAI（财务分析与规划）
- Chroma（向量库）+ DashScope Embedding
- LlamaIndex（知识库文档 ingestion / indexing）
- OpenTelemetry（Agent 执行链路追踪）
- Gunicorn（WSGI）/ Uvicorn + Nginx + Docker
- PyJWT（JWT）+ gmssl（SM2 国密）+ 阿里云 OSS

### 前端
- UniApp (Vue 3) + Vite
- 微信小程序 / H5
- Pinia 状态管理 · Vant 组件库
- SSE 流式交互
- sm-crypto（SM2 国密）

## AI 架构

请求按「快速路径 → 规划 → 执行 → 领域 Workflow → 工具」分层处理，一次用户请求由 Unified Planner 拆解为结构化任务计划，再交由 Executor 调度执行。

```
Client
  ↓
Django View / SSE Gateway
  ↓
Greeting Fast Path
  ↓
Unified Planner
  ↓
WorkflowPlan / WorkflowTask
  ↓
Executor
  ↓
Bill / Budget / Asset / Invoice / Chat Workflow
  ↓
LangChain Tools
  ↓
Service Layer
  ↓
MySQL / Redis
```

复杂财务规划：

```
Executor → Open Planning → CrewAI Finance Planner
```

知识问答：

```
Chat / Domain Workflow → RAG → Chroma / Knowledge Base
```

可观测：

```
Planner / Executor / Workflow / Tool → OpenTelemetry Trace
```

### AI 架构特点

1. **Unified Planner**：一次用户请求生成结构化 `WorkflowPlan`，任务带 `depends_on` 并按拓扑序执行。
2. **Domain Workflow**：Bill / Budget / Asset / Invoice / Chat 各自维护领域逻辑（LangGraph StateGraph），互不耦合。
3. **Tool / Service 解耦**：Workflow 负责决策，Tool 负责能力封装，Service 负责真实业务规则与数据访问；Agent 层不直接触碰 ORM。
4. **Human-in-the-loop**：写操作先做参数校验与目标定位（0 / 1 / N），再经确认卡片回传，确认状态以服务端落库为准。
5. **RAG + Memory**：内部知识库支撑财务知识问答；Chat Memory 提供多轮上下文。
6. **OpenTelemetry**：统一采集 Planner / Executor / Workflow / Tool 的执行链路。

## 项目结构

```
accountsystem/                 # Django 后端
├── account/                   # 核心记账域
│   ├── ai/                    # 福娃鸭 AI 层
│   │   ├── gateway/           # View 入口 · SSE 流式 · 寒暄快速路径
│   │   ├── orchestrator/      # Unified Planner · Executor · Memory · Trace · Response Composer
│   │   ├── agents/
│   │   │   ├── supervisor/    # 历史目录名，内部为 Bill/Budget/Asset/Invoice/Chat 领域 Workflow
│   │   │   └── crew/          # CrewAI 财务规划（finance_planner）
│   │   ├── tools/             # LangChain Tools（finance_tools）
│   │   ├── knowledge/         # RAG：data · ingestion · index · retriever · tools
│   │   └── llm/               # LLM · prompt · response · schemas
│   ├── services/              # 业务能力（碰 ORM）
│   └── views.py               # 记账 / 预算 / 资产 / 发票 / 对话接口
├── user/                      # 用户 · JWT · SM2 · 签到 · 积分 · 勋章 · 邀请
├── comment/                   # 社区：动态 · 评论 · 点赞 · 关注 · 通知
├── system/                    # 系统消息
├── common/                    # 中间件 · 初始化数据 · 响应封装
└── config/                    # dotenv · YAML 配置加载

uni_accounting/                # UniApp 前端
└── src/
    ├── pages/                 # 业务页面（记账 / 预算 / 资产 / 发票 / 统计 / 社区 / 设置）
    ├── page_langchain/        # AI 对话（langchain.vue · AgentConfirmCard · AnalysisRenderer）
    ├── components/            # Tabbar · CapsuleButton 等通用组件
    ├── api/                   # 请求封装
    ├── store/                 # Pinia：user · theme · icon
    └── utils/                 # 含 langchain_stream.js（H5 SSE）
```

## 快速开始

### 后端启动

1. 安装依赖：
```bash
cd accountsystem
pip install -r requirements.txt
```

2. 配置环境变量：
```bash
cp .env.example .env
# 编辑 .env：LLM、DashScope 等
```

3. 配置数据库 / Redis：编辑 `config/settings_debug.yaml`（本地）或 `config/settings_pro.yaml`（生产）。

4. 运行迁移：
```bash
python manage.py migrate
```

5. 初始化数据：
```bash
python manage.py shell -c "from common.initia import init_all; init_all()"
```

6. （可选）构建内部知识库向量（`chroma_db/` 不入库，本地 / 线上各自构建）：
```bash
python -m account.ai.knowledge.ingestion.build_index
```

7. 启动服务：
```bash
python manage.py runserver 0.0.0.0:8899
```

### Docker 部署

```bash
cd accountsystem
docker-compose up -d --build
```

`docker-compose.yml` 会拉起 MySQL、Redis、Gunicorn 应用与 Nginx；应用容器入口会自动等待数据库、执行迁移并初始化基础数据。

### 前端开发

```bash
cd uni_accounting
npm install
npm run dev:mp-weixin   # 微信小程序
npm run dev:h5          # H5（SSE 流式对话）
```

## 配置说明

主要环境变量（见 `accountsystem/.env.example`）：

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| DJANGO_ENV | 运行环境 debug / production | debug |
| LLM_AGENT_BASE_URL | LLM（OpenAI 兼容）地址 | https://gpt-agent.cc/v1 |
| LLM_AGENT_API_KEY | LLM API Key | — |
| LLM_AGENT_MODEL | 主模型名 | claude-sonnet-4-6 |
| LLM_MODEL_SIMPLE | 轻量任务（分类 / 摘要）模型名 | 同主模型 |
| AGENT_MAX_ITERATIONS | Agent 单轮最大迭代次数 | 4 |
| PLANNER_LLM_TIMEOUT | Planner 调用超时（秒） | 45 |
| DASHSCOPE_API_KEY | 知识库 Embedding（阿里云） | — |
| DASHSCOPE_EMBEDDING_MODEL | Embedding 模型 | text-embedding-v2 |
| KNOWLEDGE_CHROMA_DIR | 向量库持久化目录（可选） | account/ai/knowledge/chroma_db |

数据库 / Redis 等仍在 `config/settings_debug.yaml` / `config/settings_pro.yaml` 中配置。

## 许可证

MIT License
