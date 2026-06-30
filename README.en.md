# Accounting

A feature-rich personal accounting mini-program supporting income/expenses recording, budget management, asset management, AI intelligent assistant, and more.

## Features

### 💰 Accounting Functionality
- Income/expense recording with multiple categories
- Budget management with real-time tracking of budget usage
- Asset account management
- Invoice management
- 30-day income/expense reporting and statistics

### 🤖 AI Intelligent Assistant
- Intelligent dialogue powered by LangChain + LLM
- Natural language accounting (e.g., "Coffee cost 18 yuan")
- Smart bill queries (e.g., "How much did I spend this month?")
- Product usage Q&A

### 👥 Social Features
- Post updates
- Comment interaction
- Likes and follows
- User badge system
- Check-in points

### 👤 User System
- JWT authentication login
- SM2 national cryptographic encryption
- Daily check-in
- Points rewards
- Badge achievements

## Technology Stack

### Backend
- Python 3.10
- Django + Django REST Framework
- MySQL database
- Redis cache
- LangChain + Chroma vector database
- Docker deployment

### Frontend
- UniApp (Vue 3)
- WeChat Mini Program

## Project Structure

```
accountsystem/          # Django backend
├── account/           # Core accounting module
├── user/              # User module
├── comment/           # Social comment module
├── system/            # System message module
├── common/            # Common components
└── config/            # Configuration management

uni_accounting/         # UniApp frontend
└── src/
    ├── pages/         # Page components
    ├── components/    # Universal components
    ├── api/           # API requests
    ├── store/         # State management
    └── utils/         # Utility functions
```

## Quick Start

### Backend Startup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env to configure database, Redis, etc.
```

3. Run migrations:
```bash
python manage.py migrate
```

4. Initialize data:
```bash
python manage.py shell -c "from common.initia import init_all; init_all()"
```

5. Start the server:
```bash
python manage.py runserver 0.0.0.0:8899
```

### Docker Deployment

```bash
docker-compose up -d
```

### Frontend Development

```bash
cd uni_accounting
npm install
npm run dev:mp-weixin
```

## API Endpoints

| Module | Endpoint | Description |
|--------|----------|-------------|
| User | POST /api/user/login | User login |
| User | POST /api/user/register | User registration |
| Accounting | POST /api/account/save_bill | Save bill |
| Accounting | GET /api/account/bill_list | List of bills |
| Accounting | GET /api/account/bill_summary | Income/expense summary |
| Assets | POST /api/account/save_asset | Save asset |
| Assets | GET /api/account/asset_list | List of assets |
| Budget | POST /api/account/save_budget | Save budget |
| Budget | GET /api/account/budget | Budget details |
| AI | POST /api/account/langchain_chat | AI chat |
| Social | POST /api/comment/publish_post | Publish post |
| Social | POST /api/comment/publish_comment | Post comment |
| Social | POST /api/comment/like_post | Like post |

## Configuration

Main environment variables:

| Variable Name | Description | Default Value |
|---------------|-------------|---------------|
| DATABASE_URL | MySQL database connection | localhost:3306 |
| REDIS_URL | Redis connection address | localhost:6379 |
| LLM_BASE_URL | LLM API address | http://localhost:11434 |
| LLM_MODEL | Model name | qwen:7b |
| OLLAMA_BASE_URL | Ollama service address | http://localhost:11434 |

## License

MIT License