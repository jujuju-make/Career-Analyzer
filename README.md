# AI Career Agent — 智能求职分析助手

> 一个基于 **FastAPI + LangGraph + 多模型 LLM** 的智能求职分析系统，自动解析简历、分析岗位 JD、评估技能差距、优化简历、推荐实战项目，并提供 AI 模拟面试。
>
> 简历关键词：`AI Agent` `LangGraph` `FastAPI` `多模型编排` `DeepSeek` `千问` `异步架构` `MySQL/Redis`

---

## 📌 项目亮点

| 维度 | 说明 |
|------|------|
| **多 Agent 协作** | 5 个 AI Agent 各司其职（HR 视角、技术官视角、大牛视角），通过 LangGraph 有向图编排 |
| **多模型混合** | 千问负责视觉理解 + 结构化提取，DeepSeek 负责深度推理 + 严苛评估，各取所长 |
| **JD 多模态输入** | 支持文本、PDF、图片三种 JD 输入方式，千问视觉模型直接解析截图 |
| **智能面试系统** | 按需动态出题，根据回答质量决定是否追问，支持提前结束机制 |
| **LangGraph 工作流** | 并行节点（简历解析 ∥ JD 分析）+ 条件边（面试筛选决策），高效编排 |
| **角色扮演 Prompt** | 每个 Agent 设定为特定角色（HR/技术官/大牛），通过角色约束规避 LLM 过度夸赞 |
| **GitHub 项目推荐** | 根据 JD 技能要求，自动搜索 GitHub 高星项目推荐实战练习 |
| **全链路异步** | FastAPI + asyncmy + httpx，支持高并发 |

---

## 🏗 架构设计

```
用户上传简历 PDF + JD（文本/图片/PDF）
                │
                ▼
┌─────────────────────────────────────────────────┐
│              FastAPI (Uvicorn)                    │
│  POST /api/v1/resume/upload                      │
│  POST /api/v1/jd/upload-image  /upload-pdf       │
│  POST /api/v1/career/analyze                     │
│  GET  /api/v1/career/result/{id}                 │
│  POST /api/v1/interview/start  /answer           │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│           LangGraph 工作流编排                     │
│                                                   │
│  ┌──────────────┐     ┌──────────────┐           │
│  │ ResumeParser │     │ JDAnalyzer   │  ← 并行   │
│  │  (千问·HR)   │     │ (千问·技术官) │           │
│  └──────┬───────┘     └──────┬───────┘           │
│         └────────┬──────────┘                    │
│                  ▼                                │
│  ┌──────────────────────────────┐                │
│  │     GapAnalyzer (DeepSeek)   │                │
│  │     大牛视角·8级 verdict     │                │
│  └──────────────┬───────────────┘                │
│                 │                                │
│        ┌────────┴────────┐                       │
│        ▼                 ▼                       │
│  ┌────────────┐  ┌──────────────┐               │
│  │ 简历优化    │  │ 项目推荐     │  ← 并行       │
│  │ (DeepSeek)  │  │ (GitHub API) │               │
│  └────────────┘  └──────────────┘               │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│           AI 模拟面试系统                         │
│                                                   │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐   │
│  │ 简历筛选  │ →  │ 技术一面  │ →  │ 技术二面  │   │
│  │ (条件边)  │    │ (动态出题)│    │ (预留)   │   │
│  └──────────┘    └──────────┘    └─────┬────┘   │
│                                        ▼         │
│                               ┌──────────┐       │
│                               │ Leader面  │ → ... │
│                               │ (预留)    │       │
│                               └──────────┘       │
└─────────────────────────────────────────────────┘
```

### Agent 角色设计

| Agent | 模型 | 角色设定 | 核心职责 |
|-------|------|----------|----------|
| **ResumeParser** | 千问 qwen3.7-plus | 👔 资深 HR（每天看 50+ 简历，90% 前 30 秒淘汰） | 提取结构化信息、可信度评分、致命问题识别 |
| **JDAnalyzer** | 千问 qwen3.7-plus | 👨‍💼 技术面试官（面试过 300+ 候选人） | 定义真实面试标准、技能门槛、市场现实 |
| **GapAnalyzer** | DeepSeek deepseek-chat | 🧠 技术大牛（带 20 人团队，面试 500+ 人） | 8 级 verdict、严苛对比、项目可信度评估 |
| **ResumeOptimizer** | DeepSeek deepseek-chat | ✍️ 职业规划师 | 根据差距分析给出具体修改建议 |
| **ProjectRecommender** | DeepSeek deepseek-chat | 🔍 项目搜索专家 | 提取技能关键词，调用 GitHub API 推荐项目 |
| **InterviewRound1** | DeepSeek deepseek-chat | 🎤 一线技术面试官 | 按需动态出题、评估回答、追问决策 |

### 关键设计决策

- **多模型混合策略**：千问负责视觉理解（JD 截图解析）+ 结构化提取，DeepSeek 负责深度推理（差距分析、面试评估），各取所长
- **角色扮演 Prompt**：每个 Agent 设定为特定角色，通过角色约束规避 LLM 过度夸赞的倾向
- **LangGraph 有向图**：并行节点（简历解析 ∥ JD 分析）+ 条件边（面试筛选决策），高效编排
- **按需出题**：面试系统不预设题库，根据简历和 JD 动态生成题目，根据回答质量决定是否追问或提前结束
- **8 级 Verdict**：从 Strong Reject 到 Strong Yes 共 8 级，逼迫模型做更精细的区分，而非简单的"通过/不通过"

---

## 🚀 快速开始

### 前置要求

- Python 3.11+
- MySQL 8.0+
- Redis 7+
- Node.js 20+（前端开发）

### 1. 克隆项目

```bash
git clone https://github.com/jujuju-make/Career-Analyzer.git
cd Career-Analyzer
```

### 2. 配置环境变量

```bash
cp env.example .env
# 编辑 .env，至少填写：
#   DEEPSEEK_API_KEY=sk-xxx    （差距分析、面试评估）
#   QWEN_API_KEY=sk-xxx        （简历解析、JD 分析、图片理解）
#   DATABASE_URL=mysql+asyncmy://user:pass@localhost:3306/career_analyzer
#   REDIS_URL=redis://localhost:6379/0
```

### 3. 安装依赖

```bash
# 后端
pip install -r requirements.txt

# 前端
cd frontend && npm install
```

### 4. 启动服务

```bash
# 后端（终端 1）
uvicorn app.main:app --reload --port 8000

# 前端（终端 2）
cd frontend && npm run dev
```

访问 http://localhost:3000

---

## 📄 API 一览

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/resume/upload` | 上传简历 PDF，自动提取文本 |
| POST | `/api/v1/jd/upload-image` | 上传 JD 截图（千问视觉解析） |
| POST | `/api/v1/jd/upload-pdf` | 上传 JD PDF |
| POST | `/api/v1/career/analyze` | 发起完整分析（触发 LangGraph 工作流） |
| GET | `/api/v1/career/result/{id}` | 查询完整分析结果 |
| GET | `/api/v1/learning/recommend-projects` | 获取最新项目推荐 |
| GET | `/api/v1/learning/resume-optimize` | 获取最新简历优化建议 |
| POST | `/api/v1/interview/start` | 开始模拟面试 |
| POST | `/api/v1/interview/answer` | 提交面试回答 |
| GET | `/api/v1/interview/session/{id}` | 查询面试会话状态 |
| GET | `/api/v1/interview/result/{id}` | 查询面试结果 |
| GET | `/health` | 健康检查 |

---

## 📊 使用流程

```
① 上传简历 PDF
   └→ POST /api/v1/resume/upload → 返回 resume_id

② 上传 JD（三种方式之一）
   ├→ 粘贴文本
   ├→ 上传截图（千问视觉解析）
   └→ 上传 PDF

③ 发起分析
   └→ POST /api/v1/career/analyze
       body: { resume_id, target_position, job_description, jd_type }
       └→ LangGraph 工作流自动执行
           ├→ 简历解析（千问·HR视角）
           ├→ JD 分析（千问·技术官视角） ← 并行
           ├→ 差距分析（DeepSeek·大牛视角）
           ├→ 简历优化（DeepSeek） ← 并行
           └→ 项目推荐（GitHub API） ← 并行

④ 查看结果
   └→ GET /api/v1/career/result/{task_id}
       ├→ 匹配评分 + 8级 verdict
       ├→ 技能差距（不可协商 + 可培养）
       ├→ 风险信号 + 项目可信度评估
       ├→ 面试建议 + 诚实评价
       ├→ 简历优化建议
       └→ GitHub 项目推荐

⑤ 模拟面试
   └→ POST /api/v1/interview/start → 动态生成第一题
   └→ POST /api/v1/interview/answer → 评估 + 下一题
       ├→ 回答正确 → 下一题
       ├→ 部分正确 → 追问一次
       └→ 回答错误 → 直接下一题
```

---

## 🧠 Prompt 设计思路

每个 Agent 通过**角色扮演**来规避大模型过度夸赞的倾向：

### ResumeParser（HR 视角）
- 设定为"每天看 50+ 简历，90% 在前 30 秒被淘汰"
- 强制量化打分：credibility_score 有明确扣分规则
- 新增 fatal_issues 让模型必须找出"致命的"而不是"还可以"

### JDAnalyzer（技术官视角）
- 设定为"面试过 300+ 候选人"的技术面试官
- 不满足于 JD 的字面要求，而是定义"真实面试的淘汰线"
- 每个技能标注 common_pitfalls（翻车点）和 min_acceptable_evidence（最低可接受证据）

### GapAnalyzer（大牛视角）
- 设定为"带 20 人团队、面试 500+ 人、每年 1000 份只挑 10 个"的严苛专家
- match_score 明确标注"大多数候选人 30-60 分"，超 70 分需可验证证据
- 8 级 verdict 而非简单的"会/不会"，逼迫模型做更精细的区分
- 每个优势要求标注 unique_factor（稀缺性），避免模型把基本要求当优点夸

---

## 🗂 项目结构

```
Career-Agent/
├── app/
│   ├── main.py                    # FastAPI 应用入口
│   ├── core/                      # 基础设施
│   │   ├── config.py              #   环境变量配置
│   │   ├── database.py            #   异步 MySQL 引擎
│   │   └── redis_client.py        #   Redis 连接
│   ├── models/                    # 数据库模型
│   │   ├── resume.py              #   简历表
│   │   ├── analysis.py            #   分析任务 + 结果
│   │   ├── interview.py           #   面试会话 + 轮次
│   │   ├── roadmap.py             #   学习路线
│   │   └── project.py             #   项目推荐
│   ├── agents/                    # AI Agent 层
│   │   ├── base.py                #   Agent 基类
│   │   ├── llm.py                 #   LLM 客户端（千问/DeepSeek）
│   │   ├── resume_parser.py       #   简历解析（千问·HR视角）
│   │   ├── jd_analyzer.py         #   JD 分析（千问·技术官视角）
│   │   ├── gap_analyzer.py        #   差距分析（DeepSeek·大牛视角）
│   │   ├── resume_optimizer.py    #   简历优化（DeepSeek）
│   │   ├── project_recommender.py #   项目推荐（GitHub API）
│   │   └── interview_round1.py    #   技术一面（动态出题）
│   ├── workflow/                  # LangGraph 工作流
│   │   ├── orchestrator.py        #   职业分析工作流
│   │   └── interview_graph.py     #   面试工作流
│   ├── tools/                     # 工具模块
│   │   └── github_search.py       #   GitHub 项目搜索
│   ├── routers/                   # API 路由
│   │   ├── resume.py              #   简历上传
│   │   ├── jd.py                  #   JD 上传（文本/图片/PDF）
│   │   ├── career.py              #   职业分析
│   │   ├── interview.py           #   模拟面试
│   │   ├── learning.py            #   学习规划
│   │   └── project.py             #   项目推荐
│   └── services/                  # 业务逻辑
│       └── career_service.py      #   职业分析服务
├── frontend/                      # Next.js 前端
│   └── src/
│       ├── app/                   # 页面路由
│       └── lib/api/               # API 客户端
├── uploads/                       # 上传文件目录
└── requirements.txt               # Python 依赖
```

---

## 🛠 技术栈

| 层级 | 技术 |
|------|------|
| **AI 框架** | LangGraph（有向图编排） |
| **LLM** | 千问 qwen3.7-plus（视觉+结构化）+ DeepSeek deepseek-chat（深度推理） |
| **后端框架** | FastAPI (ASGI, async/await) |
| **数据库** | MySQL 8 (SQLAlchemy async + asyncmy) |
| **缓存** | Redis 7 |
| **前端** | Next.js 16 + React 19 + TailwindCSS 4 + shadcn/ui |
| **文件处理** | PyMuPDF（PDF 文本提取） |
| **外部 API** | GitHub Search API（项目推荐） |

---

## 📝 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `DEEPSEEK_API_KEY` | ✅ | DeepSeek 推理（差距分析、面试评估） |
| `QWEN_API_KEY` | ✅ | 千问推理（简历解析、JD 分析、图片理解） |
| `DATABASE_URL` | ✅ | MySQL 异步连接串 |
| `REDIS_URL` | ❌ | Redis 连接（默认 localhost:6379） |
