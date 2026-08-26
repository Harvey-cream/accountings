# 记账本 (Accounting)

个人社交记账应用：收支 / 预算 / 资产，以及 **多 Agent（福娃鸭）** 自然语言记账与分析。

## 功能特性

### 💰 记账功能
- 收入/支出记录，支持多种分类
- 预算管理，实时追踪预算使用情况
- 资产账户管理
- 发票管理
- 30天收支报表统计

### 🤖 AI 多 Agent（福娃鸭）
- **Orchestrator + Supervisor** 意图路由：`bill` / `analysis` / `budget`
- 三域独立 **LangGraph Workflow**（互不共用链）
  - Bill：记账 / 查改删；改删前定位 + 确认卡
  - Analysis：汇总 / 分类 / 对比 + 口语洞察
  - Budget：设查预算；规则校验 + 层级策略（先总后分类）
- **LangChain Tools → Service → MySQL**（Agent 不直碰 ORM）
- 内部知识库 RAG（LlamaIndex 入库 + Chroma）；`search_finance_knowledge` 挂 Analysis / Budget
- 同步对话 + H5 SSE 流式

### 👥 社交功能
- 发布动态
- 评论互动
- 点赞关注
- 用户勋章系统
- 签到积分

### 👤 用户系统
- JWT 认证登录
- SM2 国密加密
- 每日签到
- 积分奖励
- 勋章成就

## 技术栈

### 后端
- Python 3.12
- Django + Django REST Framework
- MySQL / Redis
- LangChain（LCEL / Tools）+ LangGraph（子 Agent Workflow）
- LlamaIndex（知识入库）+ Chroma + DashScope Embedding
- Docker / Nginx / Gunicorn

### 前端
- UniApp (Vue 3)
- 微信小程序 / H5

## 项目结构

```
accountsystem/                 # Django 后端
├── account/                   # 核心记账域
│   ├── ai/                    # 福娃鸭 Multi-Agent
│   │   ├── agent/             # View 入口（LCEL / SSE）
│   │   ├── orchestrator/      # 寒暄短路 · 记忆 · 路由 · 执行
│   │   ├── agents/supervisor/ # Supervisor + bill/analysis/budget 子 Agent
│   │   ├── tools/finance_tools/
│   │   ├── knowledge/         # RAG：data · ingestion · index · retriever · tools
│   │   └── llm/
│   ├── services/              # AI 业务能力（碰 ORM）
│   └── views.py
├── user/                      # 用户 · JWT · SM2 · OSS
├── comment/                   # 社区
├── system/                    # 系统消息
├── common/                    # 中间件 · 公共组件
└── config/                    # dotenv · 配置加载

uni_accounting/                # UniApp 前端
└── src/
    ├── pages/                 # 页面（含 page_langchain AI 对话）
    ├── components/
    ├── api/
    ├── store/
    └── utils/                 # 含 langchain_stream.js（SSE）
```

调用链（简图）：

```
Client → View → agent.py → orchestrator
  → Supervisor(task_type)
  → Bill / Analysis / Budget Workflow
  → finance_tools (+ knowledge tool) → services → MySQL
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
# 编辑 .env：数据库 YAML、LLM、DashScope 等
```

3. 运行迁移：
```bash
python manage.py migrate
```

4. 初始化数据：
```bash
python manage.py shell -c "from common.initia import init_all; init_all()"
```

5. （可选）构建内部知识库向量（`chroma_db/` 不入库，线上/本地各自构建）：
```bash
python -m account.ai.knowledge.ingestion.build_index
```

6. 启动服务：
```bash
python manage.py runserver 0.0.0.0:8899
```

### 前端开发

```bash
cd uni_accounting
npm install
npm run dev:mp-weixin
```

## 配置说明

主要环境变量（见 `accountsystem/.env.example`）：

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| DJANGO_ENV | 运行环境 debug / production | debug |
| LLM_AGENT_BASE_URL | LLM（OpenAI 兼容）地址 | https://gpt-agent.cc/v1 |
| LLM_AGENT_API_KEY | LLM API Key | — |
| LLM_AGENT_MODEL | 模型名 | gpt-5.4 |
| DASHSCOPE_API_KEY | 知识库 Embedding（阿里云） | — |
| DASHSCOPE_EMBEDDING_MODEL | Embedding 模型 | text-embedding-v2 |
| KNOWLEDGE_CHROMA_DIR | 向量库持久化目录（可选） | account/ai/knowledge/chroma_db |

数据库 / Redis 等仍在 `config/settings_*.yaml` 中配置。

## 许可证

MIT License
