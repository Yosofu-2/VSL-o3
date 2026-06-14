# LitManager — Intelligent Library Management System

<div align="center">

**A modern, AI-powered library management system for small to medium-sized libraries**

一款面向中小型图书馆的现代化 AI 智能图书管理系统

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-latest-green.svg)](https://fastapi.tiangolo.com/)
[![SQLite](https://img.shields.io/badge/Database-SQLite-orange.svg)](https://www.sqlite.org/)
[![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-purple.svg)](https://github.com/TomSchimansky/CustomTkinter)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()

</div>

---

## Table of Contents / 目录

- [Overview / 项目概述](#overview--项目概述)
- [Screenshots / 界面预览](#screenshots--界面预览)
- [Features / 功能特性](#features--功能特性)
- [Borrowing Rules / 借阅规则](#borrowing-rules--借阅规则)
- [Tech Stack / 技术栈](#tech-stack--技术栈)
- [System Architecture / 系统架构](#system-architecture--系统架构)
- [Database Schema / 数据库结构](#database-schema--数据库结构)
- [API Endpoints / API 端点](#api-endpoints--api-端点)
- [Installation / 安装指南](#installation--安装指南)
- [Building from Source / 源码构建](#building-from-source--源码构建)
- [Distribution / 分发与安装](#distribution--分发与安装)
- [Docker Deployment / Docker 部署](#docker-deployment--docker-部署)
- [Configuration / 配置说明](#configuration--配置说明)
- [Project Structure / 项目结构](#project-structure--项目结构)
- [Contributing / 贡献指南](#contributing--贡献指南)
- [Developers / 开发团队](#developers--开发团队)
- [License / 许可证](#license--许可证)

---

## Overview / 项目概述

**English:**

LitManager is a comprehensive desktop library management system that seamlessly combines traditional library operations with cutting-edge AI capabilities. Built with a FastAPI backend and CustomTkinter desktop GUI, it provides a modern, native-looking experience for both library administrators and readers across Windows, macOS, and Linux platforms.

The system's standout feature is its deep integration of Large Language Models (LLMs) through a unified multi-provider interface, enabling intelligent book classification via web search, natural language database queries through a conversational AI agent, and AI-assisted Excel batch import with automatic categorization.

**中文：**

LitManager 是一款综合性桌面图书管理系统，将传统图书馆运营与前沿 AI 能力无缝结合。基于 FastAPI 后端和 CustomTkinter 桌面 GUI 构建，在 Windows、macOS 和 Linux 平台上为图书馆管理员和读者提供现代化、原生外观的使用体验。

系统的核心特色是通过统一的多厂商接口深度集成大语言模型（LLM），实现基于网络搜索的智能图书分类、通过对话式 AI 代理进行自然语言数据库查询，以及支持自动分类的 AI 辅助 Excel 批量导入。

---

## Screenshots / 界面预览

> *Add screenshots here after deploying the application*
>
> *部署应用后请在此处添加界面截图*

---

## Features / 功能特性

### Admin Panel / 管理员端

| Module / 模块 | Features / 功能 |
|:---|:---|
| **Dashboard** | Real-time statistics, overdue alerts, notification badges / 实时统计、逾期提醒、通知角标 |
| **Book Management** | Full CRUD, ISBN lookup, category management, copy-level tracking, batch delete / 完整增删改查、ISBN 查询、分类管理、单册追踪、批量删除 |
| **Reader Management** | Registration, identity editing (Student/Teacher/Visitor), freeze/unfreeze, delete, password reset, Excel import/export / 注册、身份编辑（学生/教师/访客）、冻结/解冻、删除、密码重置、Excel 导入导出 |
| **Borrowing Management** | Borrow, return (two-phase confirm flow), renew, overdue tracking, pending approvals / 借书、还书（两阶段确认流程）、续借、逾期追踪、待审批管理 |
| **Statistics** | Charts for books by category/year/genre/language, borrowing trends, reader activity, top books, overdue analysis / 按分类/年份/类型/语言的图书图表、借阅趋势、读者活跃度、热门图书、逾期分析 |
| **AI Assistant** | Conversational agent with streaming output, chat history management, keyword + LLM hybrid dispatch / 带流式输出的对话代理、聊天记录管理、关键词+LLM 混合调度 |
| **Model Management** | Multi-provider LLM configuration (11+ providers), connection testing, model activation / 多厂商 LLM 配置（11+ 提供商）、连接测试、模型激活 |
| **Notifications** | System notifications, unread count, read-all, per-notification management / 系统通知、未读计数、全部已读、单条管理 |
| **Audit Logs** | Complete operation audit trail with IP and user agent tracking / 完整操作审计追踪，含 IP 和用户代理记录 |
| **AI Classification** | Web search + LLM powered book auto-classification, batch classify unclassified books / 网络搜索 + LLM 驱动的图书自动分类、批量分类未分类图书 |
| **Excel Import** | Batch import books & readers with AI-assisted classification and validation / 批量导入图书和读者，支持 AI 辅助分类和数据验证 |
| **Reservations** | Book reservation management with expiration handling / 图书预约管理，含过期处理 |
| **Fines** | Overdue fine calculation and payment tracking / 逾期罚款计算和支付追踪 |

### Reader Panel / 读者端

| Module / 模块 | Features / 功能 |
|:---|:---|
| **Book Search** | Keyword search, AI natural language search, category browsing / 关键词搜索、AI 自然语言搜索、分类浏览 |
| **My Books** | Current borrowings, borrowing history, renewal (one-time per book) / 当前借阅、借阅历史、续借（每书一次） |
| **Profile** | View/edit personal info, change password, avatar upload / 查看/编辑个人信息、修改密码、头像上传 |
| **Reservations** | Create and manage book reservations / 创建和管理图书预约 |
| **Fines** | View outstanding fines and payment status / 查看未缴罚款和支付状态 |

### AI Capabilities / AI 能力

| Feature / 功能 | Description / 说明 |
|:---|:---|
| **Conversational Agent** | Natural language database queries with keyword matching (fast) + LLM fallback (flexible) / 自然语言数据库查询，关键词匹配（快速）+ LLM 回退（灵活） |
| **Streaming Output** | Real-time typewriter-style text rendering for AI responses / AI 回复的实时打字机效果文本渲染 |
| **Intelligent Classification** | Web search to gather book metadata, LLM to determine optimal category / 网络搜索收集图书元数据，LLM 确定最佳分类 |
| **Multi-Provider LLM** | OpenAI, Anthropic, Azure OpenAI, Ollama (local), Google Gemini, and 6+ more / OpenAI、Anthropic、Azure OpenAI、Ollama（本地）、Google Gemini 等 6+ 提供商 |
| **Chat History** | Persistent conversation storage with per-conversation deletion / 持久化对话存储，支持逐条删除 |

---

## Borrowing Rules / 借阅规则

| Identity / 身份 | Borrowing Period / 借阅期限 | Max Books / 最大借阅数 | Renewal / 续借期限 |
|:---|:---:|:---:|:---:|
| **Student / 学生** | 30 days / 30 天 | 3 books / 3 本 | +15 days / +15 天 |
| **Teacher / 教师** | 180 days / 180 天 | 5 books / 5 本 | +90 days / +90 天 |
| **Visitor / 访客** | 30 days / 30 天 | Configurable / 可配置 | +15 days / +15 天 |

- Each book can be renewed **once** / 每本书可续借 **一次**
- Overdue books **cannot** be renewed / 逾期图书**不可**续借
- Two-phase return: Reader requests → Admin confirms / 两阶段还书：读者申请 → 管理员确认
- Initial reader password equals card number / 读者初始密码与卡号相同

---

## Tech Stack / 技术栈

### Backend / 后端

| Component / 组件 | Technology / 技术 |
|:---|:---|
| **Web Framework** | FastAPI |
| **Database** | SQLite (via aiosqlite) |
| **ORM** | SQLAlchemy 2.0 (Async) |
| **Data Validation** | Pydantic v2 + pydantic-settings |
| **Authentication** | JWT (python-jose) |
| **Password Hashing** | bcrypt (via passlib) |
| **HTTP Client** | httpx |
| **Excel Processing** | openpyxl |
| **Charts** | matplotlib |
| **LLM Integration** | openai, langchain, anthropic, tiktoken |
| **Web Search** | Custom web search service |

### Frontend / 前端

| Component / 组件 | Technology / 技术 |
|:---|:---|
| **GUI Framework** | CustomTkinter |
| **Charts** | matplotlib (TkAgg backend) |
| **HTTP Client** | httpx |
| **Excel Processing** | openpyxl |
| **Internationalization** | Custom i18n module (Chinese/English) |

### Build & Distribution / 构建与分发

| Component / 组件 | Technology / 技术 |
|:---|:---|
| **Executable Packaging** | PyInstaller 6.x |
| **Installer** | Inno Setup / PowerShell installer |
| **Containerization** | Docker + Docker Compose |

---

## System Architecture / 系统架构

```
┌──────────────────────────────────────────────────────────────┐
│                     Desktop GUI Layer                         │
│  ┌────────────────────┐    ┌─────────────────────────────┐  │
│  │  modern_gui.py     │    │  reader_gui.py              │  │
│  │  (Admin Panel)     │    │  (Reader Panel)             │  │
│  │                    │    │                             │  │
│  │  ──────────────┐  │    │  ┌───────────────────────┐ │  │
│  │  │APIClient     │  │    │  │APIClient              │ │  │
│  │  │(httpx)       │  │    │  │(httpx)                │ │  │
│  │  └──────┬───────┘  │    │  └───────────┬───────────┘ │  │
│  └─────────┼──────────┘    └───────────────────────────┘  │
────────────┼───────────────────────────────────────────────┘
             │         HTTP/REST API         │
             └──────────────┬────────────────┘
┌───────────────────────────▼──────────────────────────────────┐
│                      FastAPI Backend                           │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  API Routers (14 modules)                                │ │
│  │  admins · agent · audit · borrowing · conversations      │ │
│  │  copies · export · literature · models · notifications   │ │
│  │  readers · reservations · statistics · system            │ │
│  └────────────────────────┬────────────────────────────────┘ │
│                           │                                   │
│  ┌────────────────────────▼────────────────────────────────┐ │
│  │  Services                                                │ │
│  │  ──────────┐ ┌─────────────┐ ┌──────────┐ ─────────┐ │ │
│  │  │db_agent  │ │model_service│ │web_search│ │isbn_    │ │ │
│  │  │(NLP+LLM) │ │(11 providers│ │(metadata)│ │lookup   │ │ │
│  │  └──────────┘ └─────────────┘ └────────── └─────────┘ │ │
│  └────────────────────────┬────────────────────────────────┘ │
│                           │                                   │
│  ┌────────────────────────▼────────────────────────────────┐ │
│  │  Data Layer                                              │ │
│  │  ┌──────────────────┐  ┌────────────────────────────── │ │
│  │  │SQLAlchemy Models │  │Pydantic Schemas              │ │ │
│  │  │(14 tables)       │  │(request/response validation) │ │ │
│  │  └────────┬─────────  └──────────────────────────────┘ │ │
│  └───────────┼─────────────────────────────────────────────┘ │
└──────────────┼───────────────────────────────────────────────┘
               │ Async SQLAlchemy
┌──────────────▼───────────────────────────────────────────────┐
│                    SQLite Database                             │
│  llm_manager.db  (14 tables, auto-migration)                  │
└──────────────────────────────────────────────────────────────┘
```

---

## Database Schema / 数据库结构

The system uses **14 database tables** with automatic column migration for seamless upgrades:

系统使用 **14 张数据库表**，支持自动列迁移以实现无缝升级：

| Table / 表 | Description / 说明 | Key Fields / 关键字段 |
|:---|:---|:---|
| **admins** | Administrator accounts / 管理员账户 | username, password_hash |
| **readers** | Reader accounts / 读者账户 | card_number, name, identity_type, card_status, password_hash, phone, department, max_borrow, borrow_days |
| **categories** | Book categories (tree structure) / 图书分类（树形结构） | name, parent_id |
| **books** | Book titles / 图书书目 | title, author, isbn, publisher, publish_date, category_id, genre, language, pages, price, binding, description |
| **book_copies** | Individual book copies / 单册图书 | book_id, copy_number, location, condition, notes |
| **borrowing_records** | Borrowing transactions / 借阅记录 | reader_id, copy_id, borrow_date, due_date, return_date, status, renewed |
| **reservations** | Book reservations / 图书预约 | reader_id, book_id, status, expire_date |
| **fines** | Overdue fines / 逾期罚款 | reader_id, amount, paid, paid_date |
| **notifications** | System notifications / 系统通知 | title, content, is_read, user_type |
| **audit_logs** | Operation audit trail / 操作审计日志 | action, user_type, user_id, ip_address, user_agent |
| **llm_models** | LLM provider configurations / LLM 提供商配置 | name, provider, api_key_encrypted, base_url, model_type, is_active, max_tokens, temperature |
| **conversations** | AI chat sessions / AI 对话会话 | title, user_type, user_id |
| **messages** | Chat messages / 聊天消息 | conversation_id, role, content, timestamp |
| **attachments** | File attachments / 文件附件 | type, ref_id, file_path |

---

## API Endpoints / API 端点

### Authentication / 认证

| Method | Endpoint | Description / 说明 |
|:---|:---|:---|
| POST | `/api/admins/login` | Admin login / 管理员登录 |
| POST | `/api/readers/login` | Reader login / 读者登录 |

### Admin Management / 管理员管理

| Method | Endpoint | Description / 说明 |
|:---|:---|:---|
| GET | `/api/admins/` | List admins / 管理员列表 |
| POST | `/api/admins/` | Create admin / 创建管理员 |

### Book Management / 图书管理

| Method | Endpoint | Description / 说明 |
|:---|:---|:---|
| GET | `/api/books` | List/search books / 图书列表/搜索 |
| POST | `/api/books` | Create book / 创建图书 |
| GET | `/api/books/{id}` | Get book detail / 图书详情 |
| PUT | `/api/books/{id}` | Update book / 更新图书 |
| DELETE | `/api/books/{id}` | Delete book / 删除图书 |
| POST | `/api/books/batch-delete` | Batch delete / 批量删除 |
| POST | `/api/books/search-ai` | AI natural language search / AI 自然语言搜索 |
| GET | `/api/books/stats` | Book statistics / 图书统计 |
| GET | `/api/books/categories` | List categories / 分类列表 |
| POST | `/api/books/categories` | Create category / 创建分类 |
| PUT | `/api/books/categories/{id}` | Update category / 更新分类 |
| DELETE | `/api/books/categories/{id}` | Delete category / 删除分类 |
| GET | `/api/books/isbn-lookup` | ISBN lookup / ISBN 查询 |
| GET | `/api/books/uncategorized` | List unclassified books / 未分类图书 |
| POST | `/api/books/classify` | AI classify books / AI 分类图书 |
| POST | `/api/books/import` | Excel import books / Excel 导入图书 |
| POST | `/api/books/import-ai` | AI-assisted Excel import / AI 辅助导入 |
| GET | `/api/books/template` | Download import template / 下载导入模板 |

### Reader Management / 读者管理

| Method | Endpoint | Description / 说明 |
|:---|:---|:---|
| GET | `/api/readers/` | List readers / 读者列表 |
| POST | `/api/readers/` | Create reader / 创建读者 |
| GET | `/api/readers/{id}` | Get reader detail / 读者详情 |
| PUT | `/api/readers/{id}` | Update reader (identity, status, etc.) / 更新读者（身份、状态等） |
| DELETE | `/api/readers/{id}` | Delete reader / 删除读者 |
| POST | `/api/readers/import` | Excel import readers / Excel 导入读者 |
| GET | `/api/readers/{id}/profile` | Reader profile / 读者资料 |
| GET | `/api/readers/{id}/borrowings` | Reader borrowing history / 借阅历史 |
| GET | `/api/readers/{id}/overdue` | Reader overdue records / 逾期记录 |
| POST | `/api/readers/{id}/avatar` | Upload avatar / 上传头像 |
| POST | `/api/readers/{id}/reset-password` | Admin reset password / 管理员重置密码 |
| POST | `/api/readers/{id}/change-password` | Reader change password / 读者修改密码 |
| GET | `/api/readers/{id}/fines` | Reader fines / 读者罚款 |

### Borrowing / 借阅

| Method | Endpoint | Description / 说明 |
|:---|:---|:---|
| GET | `/api/borrowing/` | List borrowing records / 借阅记录列表 |
| POST | `/api/borrowing/borrow` | Borrow a book / 借书 |
| POST | `/api/borrowing/return` | Request return / 申请还书 |
| POST | `/api/borrowing/confirm-return` | Confirm return / 确认还书 |
| POST | `/api/borrowing/reject-return` | Reject return / 拒绝还书 |
| POST | `/api/borrowing/renew` | Renew book / 续借 |
| GET | `/api/borrowing/pending` | Pending returns / 待确认还书 |
| GET | `/api/borrowing/stats` | Borrowing statistics / 借阅统计 |

### Book Copies / 单册管理

| Method | Endpoint | Description / 说明 |
|:---|:---|:---|
| GET | `/api/copies/` | List copies / 单册列表 |
| POST | `/api/copies/` | Create copy / 创建单册 |
| DELETE | `/api/copies/{id}` | Delete copy / 删除单册 |

### AI Agent / AI 代理

| Method | Endpoint | Description / 说明 |
|:---|:---|:---|
| POST | `/api/agent` | Legacy chat endpoint / 旧版聊天端点 |
| POST | `/api/agent/chat` | Chat with AI (blocking) / AI 对话（阻塞） |
| POST | `/api/agent/chat-stream` | Chat with AI (SSE streaming) / AI 对话（SSE 流式） |
| GET | `/api/agent/conversations` | List conversations / 对话列表 |
| GET | `/api/agent/conversations/{id}` | Get conversation / 对话详情 |
| DELETE | `/api/agent/conversations/{id}` | Delete conversation / 删除对话 |

### Conversations / 会话管理

| Method | Endpoint | Description / 说明 |
|:---|:---|:---|
| GET | `/api/conversations` | List conversations / 会话列表 |
| GET | `/api/conversations/{id}` | Get conversation / 会话详情 |
| DELETE | `/api/conversations/{id}` | Delete conversation / 删除会话 |
| POST | `/api/conversations/chat` | Chat in conversation / 会话内聊天 |

### LLM Models / 模型管理

| Method | Endpoint | Description / 说明 |
|:---|:---|:---|
| GET | `/api/models` | List models / 模型列表 |
| GET | `/api/models/{id}` | Get model detail / 模型详情 |
| POST | `/api/models` | Create model / 创建模型 |
| PUT | `/api/models/{id}` | Update model / 更新模型 |
| DELETE | `/api/models/{id}` | Delete model / 删除模型 |
| GET | `/api/models/ollama-list` | List Ollama models / Ollama 模型列表 |
| POST | `/api/models/{id}/test` | Test model connection / 测试模型连接 |

### Statistics / 统计分析

| Method | Endpoint | Description / 说明 |
|:---|:---|:---|
| GET | `/api/stats/library` | Library overview / 图书馆概览 |
| GET | `/api/stats/books-by-category` | Books by category / 按分类统计 |
| GET | `/api/stats/books-by-year` | Books by year / 按年份统计 |
| GET | `/api/stats/borrowing-trend` | Borrowing trend / 借阅趋势 |
| GET | `/api/stats/reader-activity` | Reader activity / 读者活跃度 |
| GET | `/api/stats/top-books` | Top borrowed books / 热门图书 |
| GET | `/api/stats/genre-distribution` | Genre distribution / 类型分布 |
| GET | `/api/stats/language-distribution` | Language distribution / 语言分布 |
| GET | `/api/stats/overdue-analysis` | Overdue analysis / 逾期分析 |
| GET | `/api/stats/status-distribution` | Status distribution / 状态分布 |

### Reservations / 预约

| Method | Endpoint | Description / 说明 |
|:---|:---|:---|
| GET | `/api/reservations/my` | My reservations / 我的预约 |
| POST | `/api/reservations` | Create reservation / 创建预约 |
| DELETE | `/api/reservations/{id}` | Cancel reservation / 取消预约 |

### Notifications / 通知

| Method | Endpoint | Description / 说明 |
|:---|:---|:---|
| GET | `/api/notifications/` | List notifications / 通知列表 |
| GET | `/api/notifications/unread-count` | Unread count / 未读计数 |
| PUT | `/api/notifications/{id}/read` | Mark as read / 标记已读 |
| PUT | `/api/notifications/read-all` | Mark all read / 全部已读 |
| DELETE | `/api/notifications/{id}` | Delete notification / 删除通知 |

### Audit & System / 审计与系统

| Method | Endpoint | Description / 说明 |
|:---|:---|:---|
| GET | `/api/audit/logs` | Audit log query / 审计日志查询 |
| GET | `/api/system/backups` | List backups / 备份列表 |
| POST | `/api/system/backup` | Create backup / 创建备份 |
| POST | `/api/system/restore/{filename}` | Restore backup / 恢复备份 |
| DELETE | `/api/system/backups/{filename}` | Delete backup / 删除备份 |
| GET | `/api/health` | Health check / 健康检查 |

### Export / 导出

| Method | Endpoint | Description / 说明 |
|:---|:---|:---|
| GET | `/api/export/books` | Export books to Excel / 导出图书 |
| GET | `/api/export/readers` | Export readers to Excel / 导出读者 |
| GET | `/api/export/borrowings` | Export borrowings to Excel / 导出借阅记录 |

---

## Installation / 安装指南

### Option 1: Installer (Recommended for End Users) / 方式一：安装包（推荐终端用户）

**English:**

1. Download `LitManager-Setup-2.0.0.exe` from the Releases page
2. Run the installer and follow the wizard
3. Launch LitManager from the Start Menu or Desktop shortcut

**中文：**

1. 从 Releases 页面下载 `LitManager-Setup-2.0.0.exe`
2. 运行安装程序并按照向导操作
3. 从开始菜单或桌面快捷方式启动 LitManager

### Option 2: From Source (For Developers) / 方式二：源码安装（面向开发者）

**English:**

1. Clone the repository:
```bash
git clone https://github.com/your-username/litmanager.git
cd litmanager
```

2. Install backend dependencies:
```bash
cd backend
pip install -r requirements.txt
```

3. Install frontend dependencies:
```bash
cd ..
pip install customtkinter matplotlib openpyxl httpx
```

4. Start the backend server:
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

5. Launch the admin desktop application (new terminal):
```bash
python modern_gui.py
```

6. Launch the reader desktop application (optional, new terminal):
```bash
python reader_gui.py
```

**中文：**

1. 克隆仓库：
```bash
git clone https://github.com/your-username/litmanager.git
cd litmanager
```

2. 安装后端依赖：
```bash
cd backend
pip install -r requirements.txt
```

3. 安装前端依赖：
```bash
cd ..
pip install customtkinter matplotlib openpyxl httpx
```

4. 启动后端服务：
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

5. 启动管理员桌面应用（新终端）：
```bash
python modern_gui.py
```

6. 启动读者桌面应用（可选，新终端）：
```bash
python reader_gui.py
```

### Option 3: Docker / 方式三：Docker

```bash
docker-compose up -d
```

---

## Building from Source / 源码构建

### Prerequisites / 前置条件

- Python 3.11+
- PyInstaller 6.x (`pip install pyinstaller`)

### Build Steps / 构建步骤

```bash
# Build all executables (backend + frontend + launcher)
python build_package.py

# Create installer package
python create_installer.py
```

This produces:

| File / 文件 | Size / 大小 | Description / 说明 |
|:---|:---|:---|
| `dist_package/LitManager/LitManager.exe` | ~9 MB | Frontend GUI / 前端界面 |
| `dist_package/LitManager/LitManagerServer.exe` | ~70 MB | Backend server / 后端服务 |
| `dist_package/installer/install.bat` | — | Installer script / 安装脚本 |
| `dist_package/LitManager-files.zip` | ~79 MB | ZIP distribution / ZIP 分发包 |

### Inno Setup (Professional Installer) / Inno Setup（专业安装包）

1. Install [Inno Setup](https://jrsoftware.org/isinfo.php)
2. Open `LitManager.iss` in Inno Setup Compiler
3. Click **Compile** to generate `LitManager-Setup-2.0.0.exe`

---

## Distribution / 分发与安装

The packaged application consists of two executables managed by a launcher:

打包后的应用由启动器管理的两个可执行文件组成：

```
LitManager/
├── LitManager.exe           ← Launcher (starts server + GUI)
├── LitManagerServer.exe     ← Backend API server
└── data/                    ← Database & key files (auto-created)
    ├── llm_manager.db       ← SQLite database
    ├── .secret_key          ← JWT secret
    └── .api_key_encryption_key ← API key encryption key
```

**How it works / 工作流程：**

1. User runs `LitManager.exe`
2. Launcher starts `LitManagerServer.exe` (hidden console)
3. Launcher polls `GET /api/health` until server is ready
4. Launcher opens the CustomTkinter GUI
5. On GUI close, launcher terminates the backend server

---

## Docker Deployment / Docker 部署

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## Configuration / 配置说明

### Environment Variables / 环境变量

| Variable / 变量 | Default / 默认值 | Description / 说明 |
|:---|:---|:---|
| `SECRET_KEY` | Auto-generated | JWT signing key / JWT 签名密钥 |
| `API_KEY_ENCRYPTION_KEY` | Auto-generated | LLM API key encryption / LLM API 密钥加密 |
| `LITMAN_DB_PATH` | `./data/llm_manager.db` | Custom database path / 自定义数据库路径 |

### Configuration File / 配置文件

Create `.env` in the project root (development) or `data/` directory (packaged):

在项目根目录（开发模式）或 `data/` 目录（打包模式）创建 `.env`：

```env
# Application
APP_NAME=LitManager Library Management System
APP_VERSION=2.0.0
DEBUG=false
LOG_LEVEL=INFO

# Database
DATABASE_URL=sqlite+aiosqlite:///./llm_manager.db

# Security
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000","http://localhost:8000","http://127.0.0.1:8000"]

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=10
```

---

## Project Structure / 项目结构

```
litmanager/
── backend/
│   ├── app/
│   │   ├── routers/              # API route handlers (14 modules)
│   │   │   ├── admins.py         #   Admin management
│   │   │   ├── agent.py          #   AI agent (chat, streaming)
│   │   │   ├── audit.py          #   Audit logs
│   │   │   ├── borrowing.py      #   Borrowing workflow
│   │   │   ├── conversations.py  #   Conversation management
│   │   │   ├── copies.py         #   Book copy management
│   │   │   ├── export.py         #   Data export
│   │   │   ├── literature.py     #   Book CRUD + AI classification
│   │   │   ├── models.py         #   LLM model management
│   │   │   ├── notifications.py  #   Notification system
│   │   │   ├── readers.py        #   Reader management
│   │   │   ├── reservations.py   #   Reservation system
│   │   │   ├── statistics.py     #   Statistics & charts
│   │   │   └── system.py         #   Backup & system ops
│   │   ├── services/             # Business logic layer
│   │   │   ├── db_agent.py       #   NLP + LLM database agent
│   │   │   ├── isbn_lookup.py    #   ISBN metadata lookup
│   │   │   ├── model_service.py  #   Multi-provider LLM adapter
│   │   │   ── web_search.py     #   Web search for book info
│   │   ├── models/
│   │   │   └── model.py          # SQLAlchemy ORM models (14 tables)
│   │   ├── schemas/
│   │   │   └── model.py          # Pydantic request/response schemas
│   │   ├── config.py             # Application configuration
│   │   ├── constants.py          # System constants
│   │   ├── database.py           # Async DB engine & session
│   │   ├── main.py               # FastAPI app entry point
│   │   ├── security.py           # JWT auth & password hashing
│   │   └── utils.py              # Utility functions
│   ├── avatars/                  # Default avatar images
│   └── requirements.txt          # Backend dependencies
── modern_gui.py                 # Admin desktop application
├── reader_gui.py                 # Reader desktop application
├── api_client.py                 # HTTP API client (shared)
── i18n.py                       # Internationalization (zh/en)
├── gui_utils.py                  # GUI utility components
├── chart_widget.py               # Chart display widget
├── statistics_view.py            # Statistics view component
├── launcher.py                   # Auto-start launcher (server + GUI)
├── build_package.py              # PyInstaller build orchestrator
├── build_backend.spec            # Backend PyInstaller spec
├── build_frontend.spec           # Frontend PyInstaller spec
── build_launcher.spec           # Launcher PyInstaller spec
├── create_installer.py           # Installer package creator
├── LitManager.iss                # Inno Setup installer script
├── Dockerfile                    # Docker image definition
├── docker-compose.yml            # Docker Compose configuration
├── start.bat                     # Development start script
├── debug_start.bat               # Debug start script
├── .gitignore                    # Git ignore rules
├── README.md                     # This file
└── docs/
    └── technical.md              # Technical architecture document
```

---

## Contributing / 贡献指南

**English:**

We welcome contributions of all kinds! Whether it's bug reports, feature requests, documentation improvements, or code contributions, every bit helps.

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/your-feature`)
3. **Commit** your changes (`git commit -m 'feat: add your feature'`)
4. **Push** to the branch (`git push origin feature/your-feature`)
5. **Open** a Pull Request

Please follow [Conventional Commits](https://www.conventionalcommits.org/) for commit messages.

**中文：**

我们欢迎各种形式的贡献！无论是 Bug 报告、功能请求、文档改进还是代码贡献，每一份帮助都很重要。

1. **Fork** 本仓库
2. **创建**特性分支 (`git checkout -b feature/your-feature`)
3. **提交**更改 (`git commit -m 'feat: add your feature'`)
4. **推送**到分支 (`git push origin feature/your-feature`)
5. **提交** Pull Request

请使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范编写提交信息。

### Commit Convention / 提交规范

| Prefix / 前缀 | Description / 说明 |
|:---|:---|
| `feat:` | New feature / 新功能 |
| `fix:` | Bug fix / Bug 修复 |
| `docs:` | Documentation changes / 文档变更 |
| `style:` | Code style (formatting, etc.) / 代码风格 |
| `refactor:` | Code refactoring / 代码重构 |
| `test:` | Adding/updating tests / 添加/更新测试 |
| `chore:` | Build process, dependencies / 构建流程、依赖 |

---

## Developers / 开发团队

### Core Development / 核心开发

| Name / 姓名 | Role / 角色 | Contact / 联系方式 |
|:---|:---|:---|
| [Yosofu_2] | Lead Developer / 首席开发 | [3380683595@qq.com] |

### Technology Partners / 技术合作伙伴

- [FastAPI](https://fastapi.tiangolo.com/) — Modern Python web framework
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) — Modern Python GUI toolkit
- [SQLAlchemy](https://www.sqlalchemy.org/) — Python SQL toolkit and ORM
- [PyInstaller](https://pyinstaller.org/) — Python application bundler
- [Inno Setup](https://jrsoftware.org/isinfo.php) — Windows installer creator

### Special Thanks / 特别感谢

- All open-source contributors whose libraries power this project
- The Python community for continuous innovation
- Early testers and feedback providers

---

## License / 许可证

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

本项目采用 **MIT 许可证** — 详见 [LICENSE](LICENSE) 文件。

---

## Changelog / 更新日志

### v2.0.0 (Current / 当前版本)

**English:**
- AI-powered conversational database agent with streaming output
- Multi-provider LLM support (11+ providers including Ollama local models)
- Intelligent book classification via web search + LLM
- Identity-based borrowing rules (Student: 30d/3 books, Teacher: 180d/5 books)
- Book renewal system with one-time renewal per book
- Reader identity management (edit, freeze/unfreeze, delete)
- Two-phase return workflow (reader request → admin confirm)
- Comprehensive statistics dashboard with 10 chart types
- Excel batch import/export with AI-assisted classification
- Full audit logging system
- Reader password management (bcrypt hashing, self-service change)
- Reservation and fine management systems
- Bilingual UI (Chinese/English) with seamless switching
- PyInstaller packaging with auto-launch installer
- Docker deployment support

**中文：**
- AI 驱动对话式数据库代理，支持流式输出
- 多厂商 LLM 支持（11+ 提供商，含 Ollama 本地模型）
- 基于网络搜索 + LLM 的智能图书分类
- 基于身份类型的借阅规则（学生：30 天/3 本，教师：180 天/5 本）
- 图书续借系统，每书可续借一次
- 读者身份管理（编辑、冻结/解冻、删除）
- 两阶段还书工作流（读者申请 → 管理员确认）
- 全面统计仪表板，含 10 种图表类型
- Excel 批量导入/导出，支持 AI 辅助分类
- 完整审计日志系统
- 读者密码管理（bcrypt 加密、自助修改）
- 预约和罚款管理系统
- 双语界面（中/英），无缝切换
- PyInstaller 打包，含自动启动安装程序
- Docker 部署支持

---

<div align="center">

**Made by the LitManager Team**

**由 LitManager 团队打造**

[![GitHub stars](https://img.shields.io/github/stars/your-username/litmanager?style=social)](https://github.com/your-username/litmanager)
[![GitHub forks](https://img.shields.io/github/forks/your-username/litmanager?style=social)](https://github.com/your-username/litmanager)
[![GitHub issues](https://img.shields.io/github/issues/your-username/litmanager)](https://github.com/your-username/litmanager/issues)

</div>
