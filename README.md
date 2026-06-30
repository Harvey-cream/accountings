

# 记账本 (Accounting)

一个功能完善的个人记账小程序，支持收支记录、预算管理、资产管理、AI智能助手等功能。

## 功能特性

### 💰 记账功能
- 收入/支出记录，支持多种分类
- 预算管理，实时追踪预算使用情况
- 资产账户管理
- 发票管理
- 30天收支报表统计

### 🤖 AI 智能助手
- 基于 LangChain + LLM 的智能对话
- 自然语言记账 ("咖啡花了18元")
- 智能查询账单 ("本月花了多少钱")
- 产品使用问答

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
- Python 3.10
- Django + Django REST Framework
- MySQL 数据库
- Redis 缓存
- LangChain + Chroma 向量库
- Docker 部署

### 前端
- UniApp (Vue 3)
- 微信小程序

## 项目结构

```
accountsystem/          # Django 后端
├── account/           # 核心记账模块
├── user/              # 用户模块
├── comment/           # 社交评论模块
├── system/            # 系统消息模块
├── common/            # 公共组件
└── config/            # 配置管理

uni_accounting/         # UniApp 前端
└── src/
    ├── pages/         # 页面组件
    ├── components/    # 通用组件
    ├── api/          # API 请求
    ├── store/       # 状态管理
    └── utils/        # 工具函数
```

## 快速开始

### 后端启动

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 配置环境变量：
```bash
cp .env.example .env
# 编辑 .env 配置数据库、Redis 等
```

3. 运行迁移：
```bash
python manage.py migrate
```

4. 初始化数据：
```bash
python manage.py shell -c "from common.initia import init_all; init_all()"
```

5. 启动服务：
```bash
python manage.py runserver 0.0.0.0:8899
```

### Docker 部署

```bash
docker-compose up -d
```

### 前端开发

```bash
cd uni_accounting
npm install
npm run dev:mp-weixin
```

## API 接口

| 模块 | 接口 | 说明 |
|------|------|------|
| 用户 | POST /api/user/login | 用户登录 |
| 用户 | POST /api/user/register | 用户注册 |
| 记账 | POST /api/account/save_bill | 保存账单 |
| 记账 | GET /api/account/bill_list | 账单列表 |
| 记账 | GET /api/account/bill_summary | 收支汇总 |
| 资产 | POST /api/account/save_asset | 保存资产 |
| 资产 | GET /api/account/asset_list | 资产列表 |
| 预算 | POST /api/account/save_budget | 保存预算 |
| 预算 | GET /api/account/budget | 预算详情 |
| AI | POST /api/account/langchain_chat | AI 对话 |
| 社交 | POST /api/comment/publish_post | 发布动态 |
| 社交 | POST /api/comment/publish_comment | 发表评论 |
| 社交 | POST /api/comment/like_post | 点赞 |

## 配置说明

主要环境变量：

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| DATABASE_URL | MySQL 数据库连接 | localhost:3306 |
| REDIS_URL | Redis 连接地址 | localhost:6379 |
| LLM_BASE_URL | LLM API 地址 | http://localhost:11434 |
| LLM_MODEL | 模型名称 | qwen:7b |
| OLLAMA_BASE_URL | Ollama 服务地址 | http://localhost:11434 |

## 许可证

MIT License