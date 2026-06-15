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
│   │   ├── config.py             #   环境变量加载（密钥、数据库、模型配置）
│   │   ├── database.py           #   异步 MySQL 引擎 + Session + 自动建表
│   │   └── redis_client.py       #   Redis 连接（预留）
│   │
│   ├── models/                   # 数据库表（SQLAlchemy ORM）
│   │   ├── resume.py             #   简历表（id, filename, file_path, parsed_content, status）
│   │   ├── analysis.py           #   分析任务 + 完整分析结果（含大牛评价9个字段 + 项目推荐）
│   │   ├── roadmap.py            #   学习路线表（预留）
│   │   ├── interview.py          #   面试题表（预留）
│   │   └── project.py            #   项目推荐表（预留）
│   │
│   ├── schemas/                  # 请求/响应格式（Pydantic 校验）
│   │   ├── resume.py             #   上传简历响应
│   │   ├── analysis.py           #   分析请求（含 jd_type） + 结果
│   │   ├── interview.py          #   面试题（预留）
│   │   ├── project.py            #   项目推荐（预留）
│   │   └── common.py             #   通用 Schema
│   │
│   ├── agents/                   # AI Agent（LLM 调用层）
│   │   ├── base.py               #   Agent 基类（抽象 run 方法）
│   │   ├── llm.py                #   LLM 客户端（千问/DeepSeek，含图片视觉能力）
│   │   ├── resume_parser.py      #   简历解析 → 千问（HR 视角：挑刺打分、可信度评估）
│   │   ├── jd_analyzer.py        #   JD 分析   → 千问（技术官视角：真实面试标准）
│   │   ├── gap_analyzer.py       #   差距分析  → DeepSeek（大牛视角：严苛评价、8级 verdict）
│   │   ├── resume_optimizer.py   #   简历优化  → DeepSeek（根据差距分析给出修改建议）
│   │   ├── project_recommender.py #  项目推荐  → 调用 GitHub Search 工具推荐实战项目
│   │   ├── resume_jd_analyzer.py #   合并版 Agent（预留/备选，把前两步合并为一次调用）
│   │   ├── interview_prep.py     #   面试准备（预留）
│   │   └── roadmap_generator.py  #   学习路线（预留）
│   │
│   ├── tools/                    # 独立工具模块
│   │   ├── __init__.py           #   工具模块初始化
│   │   └── github_search.py      #   GitHub Search API 封装（按 stars 排序搜索项目）
│   │
│   ├── workflow/                 # Agent 工作流编排
│   │   └── orchestrator.py       #   LangGraph 有向图（5个节点：parse_resume ∥ analyze_jd → analyze_gap → optimize_resume ∥ recommend_projects）
│   │
│   ├── routers/                  # API 路由（用户接口）
│   │   ├── resume.py             #   POST /api/v1/resume/upload（上传 PDF，自动提取文本）
│   │   ├── career.py             #   POST /api/v1/career/analyze（触发完整工作流）
│   │   │                         #   GET  /api/v1/career/result/{id}（查询完整分析结果）
│   │   ├── jd.py                 #   POST /api/v1/jd/upload-image（上传 JD 截图）
│   │   │                         #   POST /api/v1/jd/upload-pdf（上传 JD PDF）
│   │   ├── learning.py           #   GET  /api/v1/learning/recommend-projects（获取最新项目推荐）
│   │   ├── interview.py          #   面试题接口（预留）
│   │   └── project.py            #   项目推荐接口（预留）
│   │
│   └── services/                 # 业务逻辑层（预留，当前逻辑在路由层）
│       └── career_service.py
│
└── uploads/                      # 上传文件目录（PDF、JD图片，gitignore）
```

## 核心工作流

```
① 用户上传简历 PDF
   └─→ POST /api/v1/resume/upload
       └─→ 保存文件 → PyMuPDF 提取文本 → 入库 resumes 表

② 用户上传 JD（三种方式之一）
   ├─→ POST /api/v1/jd/upload-image（截图 → 保存到 ./uploads/jd_xxx.png）
   ├─→ POST /api/v1/jd/upload-pdf（PDF → 保存到 ./uploads/jd_xxx.pdf）
   └─→ 直接传文本（JD 全文）

③ 用户发起分析
   └─→ POST /api/v1/career/analyze
       body: { resume_id, job_description（文本/图片路径）, jd_type（text/image/pdf）}
       └─→ app/workflow/orchestrator.py（LangGraph 有向图）

           ┌─ Node1: parse_resume ──────────────────┐
           │  ResumeParserAgent（千问 qwen3.7-plus） │
           │  输入: state["resume_file_path"]        │
           │  流程: PDF → 文本 → 千问（HR 视角）     │
           │  输出: resume_parsed = {                │
           │    raw_text: "...",                     │
           │    structured: {                        │
           │      name, education, work_history,     │
           │      core_skills, projects,             │
           │      red_flags, credibility_score,      │
           │      fatal_issues, overall_impression   │
           │    }                                    │
           │  }                                      │
           └─────────────────────────────────────────┘
                                  │
           ┌─ Node2: analyze_jd ─────────────────────┐  ← 与 Node1 并行
           │  JDAnalyzerAgent（千问 qwen3.7-plus）    │
           │  输入: state["jd_input"]                 │
           │  流程:                                    │
           │    ├─ 文本 → 千问                         │
           │    ├─ 图片 → base64 → 千问视觉模型        │
           │    └─ PDF  → PyMuPDF → 千问              │
           │  输出: jd_analysis = {                   │
           │    raw_text/raw_image_path: "...",       │
           │    analysis: {                           │
           │      core_skills（含real_world_bar,      │
           │        common_pitfalls, min_acceptable）,│
           │      market_reality（含filter_rate）,    │
           │      experience_requirement, ...         │
           │    }                                     │
           │  }                                       │
           └─────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │   两者都完成，进入 Node3    │
                    └─────────────┬─────────────┘
                                  │
           ┌─ Node3: analyze_gap ────────────────────┐
           │  GapAnalyzerAgent（DeepSeek deepseek-chat）│
           │  输入: state["resume_parsed"]            │
           │        + state["jd_analysis"]            │
           │  流程: DeepSeek 大牛视角对比分析         │
           │  输出: gap_analysis = {                  │
           │    overall_verdict（8级: Strong Reject → Strong Yes）,│
           │    match_score（0-100，基准：多数人30-60）,│
           │    critical_gaps（non_negotiable + trainable）,│
           │    strengths（含 unique_factor 稀缺性）, │
           │    red_flags（含 probe_question）,        │
           │    project_credibility（含 red_herring）, │
           │    interview_recommendation（含 alternative）,│
           │    career_trajectory_analysis,            │
           │    honest_assessment                     │
           │  }                                       │
           └─────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────────────┐
                    │  Node4 和 Node5 并行执行           │
                    ├───────────────────────────────────┤
           ┌─ Node4: optimize_resume ────────────────┐  │
           │  ResumeOptimizationAgent（DeepSeek）     │  │
           │  输入: state["resume_parsed"]            │  │
           │        + state["gap_analysis"]           │  │
           │  输出: optimition（简历修改建议文本）     │  │
           └─────────────────────────────────────────┘  │
                                                        │
           ┌─ Node5: recommend_projects ──────────────┐  │
           │  ProjectRecommenderAgent                 │  │
           │  输入: state["jd_analysis"]               │  │
           │  流程: 提取技能 → 调用 GitHub Search API  │  │
           │  输出: project_recommendations = [        │  │
           │    { name, url, description, stars,       │  │
           │      forks, language, topics }            │  │
           │  ]                                        │  │
           └─────────────────────────────────────────┘  │
                                  │                     │
                    ┌─────────────┴─────────────────────┘
                    │  全部存入 AnalysisResult 表
                    │  返回 task_id 给用户
                    └───────────────────────────┘

④ 用户查询结果
   └─→ GET /api/v1/career/result/{task_id}
       └─→ 从 analysis_results 表读取，返回完整 JSON
           ├─ 匹配摘要：match_score, strengths, missing_skills, summary
           ├─ 大牛评价：overall_verdict, red_flags, honest_assessment, ...
           ├─ 面试建议：interview_recommendation（含考察重点）
           ├─ 原始分析：resume_structured, jd_analysis
           └─ 项目推荐：project_recommendations（3 个 GitHub 项目）

⑤ 用户获取项目推荐（无需传参，自动取最新）
   └─→ GET /api/v1/learning/recommend-projects
       └─→ 从 analysis_results 表读取最新一条的 project_recommendations
```

## API 一览

| 接口 | 方法 | 说明 | 位置 |
|------|------|------|------|
| `/api/v1/resume/upload` | POST | 上传简历 PDF，自动提取文本 | `routers/resume.py` |
| `/api/v1/jd/upload-image` | POST | 上传 JD 截图（.png/.jpg等） | `routers/jd.py` |
| `/api/v1/jd/upload-pdf` | POST | 上传 JD PDF | `routers/jd.py` |
| `/api/v1/career/analyze` | POST | 发起完整分析（文本/图片/PDF 三种 JD 输入） | `routers/career.py` |
| `/api/v1/career/result/{id}` | GET | 查询完整分析结果 | `routers/career.py` |
| `/api/v1/learning/recommend-projects` | GET | 获取最新分析的 GitHub 项目推荐（无需传参） | `routers/learning.py` |

## 模型分配

| Agent | 模型 | 角色 | 位置 |
|-------|------|------|------|
| ResumeParser | 千问 qwen3.7-plus | 👔 资深 HR（挑刺、可信度评估、致命问题） | `agents/resume_parser.py` |
| JDAnalyzer | 千问 qwen3.7-plus | 👨‍💼 技术面试官（真实面试标准、淘汰线） | `agents/jd_analyzer.py` |
| GapAnalyzer | DeepSeek deepseek-chat | 🧠 技术大牛（严苛对比、8级 verdict） | `agents/gap_analyzer.py` |
| ResumeOptimization | DeepSeek deepseek-chat | ✍️ 简历优化师（根据差距分析给出修改建议） | `agents/resume_optimizer.py` |
| ProjectRecommender | DeepSeek deepseek-chat | 🔍 项目搜索专家（生成搜索关键词，调用 GitHub API） | `agents/project_recommender.py` |

## 工具模块

| 工具 | 说明 | 位置 |
|------|------|------|
| `search_github_projects` | 按关键词搜索 GitHub 项目，按 stars 排序 | `tools/github_search.py` |
| `search_github_projects_by_skills` | 按技能列表搜索，自动去重排序 | `tools/github_search.py` |

## 数据库表

| 表名 | 关键字段 | 说明 |
|------|---------|------|
| `resumes` | id, filename, file_path, parsed_content, status | 上传的简历 |
| `analysis_tasks` | id, resume_id, job_description, status | 每次分析任务 |
| `analysis_results` | id, task_id, gap_analysis, resume_structured, jd_analysis, **project_recommendations** | 完整分析结果（含项目推荐） |

## 三个 Agent 的 Prompt 设计思路

每个 Agent 通过**角色扮演**来规避大模型过度夸赞的倾向：

### ResumeParser（HR 视角）
- 设定为"每天看50+简历，90%在前30秒被淘汰"
- 强制量化打分：credibility_score 有明确扣分规则
- 新增 fatal_issues 让模型必须找出"致命的"而不是"还可以"

### JDAnalyzer（技术官视角）
- 设定为"面试过300+候选人"的技术面试官
- 不满足于 JD 的字面要求，而是定义"真实面试的淘汰线"
- 每个技能标注 common_pitfalls（翻车点）和 min_acceptable_evidence（最低可接受证据）

### GapAnalyzer（大牛视角）
- 设定为"带20人团队、面试500+人、每年1000份只挑10个"的严苛专家
- match_score 明确标注"大多数候选人30-60分"，超70分需可验证证据
- 8级 verdict 而非简单的"会/不会"，逼迫模型做更精细的区分
- 每个优势要求标注 unique_factor（稀缺性），避免模型把基本要求当优点夸
