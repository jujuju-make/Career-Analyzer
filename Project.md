# AI Career Agent — 项目地图

## 目录结构

```
Career-Agent/
├── .env                          # 环境变量（API Key、数据库配置）
├── requirements.txt              # Python 依赖
├── Project.md                    # ← 当前文件
│
├── app/
│   ├── main.py                   # FastAPI 入口 + 路由注册 + 启动建表
│   │
│   ├── core/                     # 基础设施
│   │   ├── config.py             #   环境变量加载
│   │   ├── database.py           #   异步 MySQL 引擎 + Session
│   │   └── redis_client.py       #   Redis 连接（预留）
│   │
│   ├── models/                   # 数据库表（SQLAlchemy）
│   │   ├── resume.py             #   简历表
│   │   ├── analysis.py           #   分析任务表 + 分析结果表
│   │   ├── roadmap.py            #   学习路线表（预留）
│   │   ├── interview.py          #   面试题表（预留）
│   │   └── project.py            #   项目推荐表（预留）
│   │
│   ├── schemas/                  # 请求/响应格式（Pydantic）
│   │   ├── resume.py             #   上传简历响应
│   │   ├── analysis.py           #   分析请求 + 结果
│   │   ├── interview.py          #   面试题（预留）
│   │   ├── project.py            #   项目推荐（预留）
│   │   └── common.py             #   通用 Schema
│   │
│   ├── agents/                   # AI Agent（LLM 调用）
│   │   ├── base.py               #   Agent 基类
│   │   ├── llm.py                #   LLM 客户端（千问/DeepSeek）
│   │   ├── resume_parser.py      #   简历解析 → 千问
│   │   ├── jd_analyzer.py        #   JD 分析   → 千问
│   │   ├── gap_analyzer.py       #   差距分析  → DeepSeek
│   │   └── ...roadmap等          #   预留
│   │
│   ├── workflow/                 # Agent 工作流编排
│   │   └── orchestrator.py       #   LangGraph 图（3个节点）
│   │
│   ├── routers/                  # API 路由
│   │   ├── resume.py             #   POST /api/v1/resume/upload
│   │   └── career.py             #   POST /api/v1/career/analyze
│   │                             #   GET  /api/v1/career/result/{id}
│   │
│   └── services/                 # 业务逻辑层
│       └── career_service.py     #   （预留，当前逻辑在路由层）
│
└── uploads/                      # 上传的 PDF 文件（gitignore）
```

## 核心工作流

```
① 用户上传简历 PDF
   └─→ app/routers/resume.py → 保存文件 + fitz 提取文本 → 入库

② 用户发起分析（传入 resume_id + JD 文本）
   └─→ app/routers/career.py
       └─→ app/workflow/orchestrator.py（LangGraph）
           ├── ResumeParser（千问）  → 解析简历
           ├── JDAnalyzer（千问）    → 分析 JD          ← 并行
           └── GapAnalyzer（DeepSeek）→ 技能差距分析    ← 等前两者完成
                └─→ 结果存入 MySQL → 返回 task_id
```

## API 一览

| 接口 | 说明 | 位置 |
|------|------|------|
| `POST /api/v1/resume/upload` | 上传简历 PDF | `app/routers/resume.py` |
| `POST /api/v1/career/analyze` | 触发完整分析工作流 | `app/routers/career.py` |
| `GET /api/v1/career/result/{id}` | 查询分析结果 | `app/routers/career.py` |

## 模型分配

| Agent | 模型 | 位置 |
|-------|------|------|
| 简历解析 | 千问 (qwen-plus) | `app/agents/resume_parser.py` |
| JD 分析 | 千问 (qwen-plus) | `app/agents/jd_analyzer.py` |
| 差距分析 | DeepSeek (deepseek-chat) | `app/agents/gap_analyzer.py` |
