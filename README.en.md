# Accounting

An AI-enhanced personal finance platform for bookkeeping, budgeting, asset and invoice management, financial insights, community interaction, and natural-language finance workflows powered by RAG and agent-based orchestration. The built-in assistant, **FuWa Duck**, is the platform's intelligent interaction and task-execution layer — not the product itself.

## Features

### 💰 Finance Management
- Income / expense bookkeeping with multi-category bills (category and icon management)
- Bill querying with date / type filters, editing, and deletion
- Income & expense statistics: overview, monthly / yearly summaries, category rankings, trend charts
- Budgeting: yearly / monthly / category budgets at multiple levels, with real-time usage tracking and overrun constraints
- Asset accounts: asset / liability accounts, balances, net-worth summary, balance adjustments
- Invoice management: issuer, tax ID, amount, and related details

### 🤖 AI Finance Assistant (FuWa Duck)
- Natural-language bookkeeping — single or batch, with amount / category / date parsing
- Natural-language queries over bills, budgets, assets, and invoices
- Natural-language operations — update bills, adjust budgets, create assets, maintain invoices
- Finance knowledge Q&A backed by an internal knowledge base (RAG)
- Financial analysis & planning — multi-role CrewAI reports
- Multi-turn chat memory for continuous context
- Human-in-the-loop confirmation for write operations (validation, target resolution, confirm cards)
- Streaming H5 responses (SSE) with live execution status and token-by-token replies

### 👥 Community & Social
- Publish posts (text + images)
- Likes
- Comments
- Follows
- Notifications

### 👤 User & Growth System
- JWT authentication
- SM2 national cryptographic encryption
- User profile & avatar upload (Alibaba Cloud OSS)
- Daily check-in
- Points rewards
- Badge achievements
- Invite QR code
- Personalized themes (multiple color schemes)

## Technology Stack

### Backend
- Python 3.12
- Django + Django REST Framework
- MySQL 8 / Redis 7
- LangChain (LCEL / Tools) + LangGraph (domain workflows)
- CrewAI (financial analysis & planning)
- Chroma (vector store) + DashScope Embedding
- LlamaIndex (knowledge-base ingestion / indexing)
- OpenTelemetry (agent execution tracing)
- Gunicorn (WSGI) / Uvicorn + Nginx + Docker
- PyJWT (JWT) + gmssl (SM2) + Alibaba Cloud OSS

### Frontend
- UniApp (Vue 3) + Vite
- WeChat Mini Program / H5
- Pinia state management · Vant components
- SSE streaming
- sm-crypto (SM2)

## AI Architecture

Requests flow through a layered pipeline: greeting fast path → planning → execution → domain workflows → tools. A single user request is decomposed by the Unified Planner into a structured task plan and dispatched by the Executor.

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

Complex financial planning:

```
Executor → Open Planning → CrewAI Finance Planner
```

Knowledge Q&A:

```
Chat / Domain Workflow → RAG → Chroma / Knowledge Base
```

Observability:

```
Planner / Executor / Workflow / Tool → OpenTelemetry Trace
```

### Design Highlights

1. **Unified Planner** — one request becomes a structured `WorkflowPlan`; tasks carry `depends_on` and run in topological order.
2. **Domain Workflows** — Bill / Budget / Asset / Invoice / Chat each own their domain logic (LangGraph StateGraph) without cross-coupling.
3. **Tool / Service separation** — workflows decide, tools encapsulate capabilities, services own business rules and data access; agents never touch the ORM directly.
4. **Human-in-the-loop** — write operations are validated and target-resolved (0 / 1 / N) before a confirm card round-trip; confirmation state is server-persisted.
5. **RAG + Memory** — an internal knowledge base powers finance Q&A, while chat memory provides multi-turn context.
6. **OpenTelemetry** — end-to-end tracing across Planner / Executor / Workflow / Tool.

## Project Structure

```
accountsystem/                 # Django backend
├── account/                   # Core accounting domain
│   ├── ai/                    # FuWa Duck AI layer
│   │   ├── gateway/           # View entry · SSE streaming · greeting fast path
│   │   ├── orchestrator/      # Unified Planner · Executor · Memory · Trace · Response Composer
│   │   ├── agents/
│   │   │   ├── supervisor/    # Historical directory name; holds Bill/Budget/Asset/Invoice/Chat domain workflows
│   │   │   └── crew/          # CrewAI financial planning (finance_planner)
│   │   ├── tools/             # LangChain tools (finance_tools)
│   │   ├── knowledge/         # RAG: data · ingestion · index · retriever · tools
│   │   └── llm/               # LLM · prompt · response · schemas
│   ├── services/              # Business services (touch the ORM)
│   └── views.py               # Bill / budget / asset / invoice / chat endpoints
├── user/                      # User · JWT · SM2 · check-in · points · badges · invites
├── comment/                   # Community: posts · comments · likes · follows · notices
├── system/                    # System messages
├── common/                    # Middleware · seed data · response helpers
└── config/                    # dotenv · YAML config loading

uni_accounting/                # UniApp frontend
└── src/
    ├── pages/                 # Business pages (bills / budget / assets / invoices / charts / community / settings)
    ├── page_langchain/        # AI chat (langchain.vue · AgentConfirmCard · AnalysisRenderer)
    ├── components/            # Shared components (Tabbar · CapsuleButton)
    ├── api/                   # Request layer
    ├── store/                 # Pinia: user · theme · icon
    └── utils/                 # Includes langchain_stream.js (H5 SSE)
```

## Quick Start

### Backend

1. Install dependencies:
```bash
cd accountsystem
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env: LLM, DashScope, etc.
```

3. Configure database / Redis: edit `config/settings_debug.yaml` (local) or `config/settings_pro.yaml` (production).

4. Run migrations:
```bash
python manage.py migrate
```

5. Seed initial data:
```bash
python manage.py shell -c "from common.initia import init_all; init_all()"
```

6. (Optional) Build the knowledge-base vectors (`chroma_db/` is not committed — build per environment):
```bash
python -m account.ai.knowledge.ingestion.build_index
```

7. Start the server:
```bash
python manage.py runserver 0.0.0.0:8899
```

### Docker

```bash
cd accountsystem
docker-compose up -d --build
```

`docker-compose.yml` brings up MySQL, Redis, the Gunicorn app, and Nginx. The app entrypoint waits for the database, runs migrations, and seeds base data automatically.

### Frontend

```bash
cd uni_accounting
npm install
npm run dev:mp-weixin   # WeChat Mini Program
npm run dev:h5          # H5 (SSE streaming chat)
```

## Configuration

Main environment variables (see `accountsystem/.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| DJANGO_ENV | Runtime environment: debug / production | debug |
| LLM_AGENT_BASE_URL | LLM endpoint (OpenAI-compatible) | https://api4.mygptlife.com/v1/ |
| LLM_AGENT_API_KEY | LLM API key | — |
| LLM_AGENT_MODEL | Primary model name | claude-sonnet-4-6 |
| LLM_AGENT_FALLBACK_MODELS | Candidate models (comma-separated): chain = primary + the rest, tried in order | claude-sonnet-4-6,gpt-5.6-luna,gemini-3.7-flash |
| LLM_MODEL_SIMPLE | Lightweight model for classification / summaries | Same as primary |
| AGENT_MAX_ITERATIONS | Max agent iterations per turn | 4 |
| PLANNER_LLM_TIMEOUT | Planner request timeout (seconds) | 45 |
| DASHSCOPE_API_KEY | Knowledge-base embedding (Alibaba Cloud) | — |
| DASHSCOPE_EMBEDDING_MODEL | Embedding model | text-embedding-v2 |
| KNOWLEDGE_CHROMA_DIR | Vector-store persist directory (optional) | account/ai/knowledge/chroma_db |

Database / Redis settings live in `config/settings_debug.yaml` / `config/settings_pro.yaml`.

## License

MIT License
