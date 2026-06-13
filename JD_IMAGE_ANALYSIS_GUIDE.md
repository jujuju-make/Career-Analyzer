# JD 图片解析功能指南

## 概述

本项目已升级支持**JD 图片输入**，现在用户可以通过上传 JD 的截图或图片来进行岗位分析，系统会使用**千问的视觉能力**自动解析图片中的内容。

## 核心改进

### 1. 三个 Agent 的 Prompt 优化（角色扮演）

#### ResumeParserAgent（HR 视角）
- **身份**：资深 HR 招聘官，10年+ 经验
- **核心能力**：
  - 识别职业发展的连贯性
  - 发现职位跳跃的风险信号
  - 评估简历的真实性和可信度
- **新增字段**：
  - `red_flags`：HR 角度的风险信号
  - `credibility_score`：项目可信度评分（1-10）
  - `professionalism_score`：简历专业度评分

#### JDAnalyzerAgent（技术面试官视角）
- **身份**：公司首席技术面试官
- **核心能力**：
  - 区分"看起来会"和"真的会"
  - 了解市场竞争的现实情况
  - 精准定义不同技能的考察方法
- **支持的输入**：
  - 文本输入（直接粘贴 JD）
  - PDF 输入（自动提取文本）
  - **图片输入（新）**（使用千问的视觉能力）

#### GapAnalyzerAgent（技术大牛视角）
- **身份**：行业大牛，15年+ 经验
- **核心能力**：
  - 看穿简历包装，识别真实能力
  - 严苛评估候选人的竞争力
  - 区分虚假宣传 vs 真实贡献
- **关键输出**：
  - `project_credibility`：项目描述真实性评估
  - `honest_assessment`：最诚实的看法（避免虚浮夸赞）
  - `interview_recommendation`：是否邀请面试 + 理由

---

## 功能使用流程

### 方式 1：直接输入文本 JD

```bash
POST /api/v1/career/analyze

{
  "resume_id": "resume_abc123",
  "target_position": "AI Agent 开发实习生",
  "job_description": "我们正在招聘 AI Agent 开发实习生...",
  "jd_type": "text"  # 文本类型
}
```

### 方式 2：上传 JD 图片

**第一步：上传 JD 图片**

```bash
POST /api/v1/jd/upload-image

Content-Type: multipart/form-data
file: <JD 截图文件>
```

响应示例：
```json
{
  "jd_image_path": "./uploads/jd_abc123def456.png",
  "filename": "jd_screenshot.png",
  "status": "uploaded",
  "message": "JD 图片上传成功，请在分析时使用这个路径作为 job_description，并将 jd_type 设置为 image"
}
```

**第二步：使用图片路径进行分析**

```bash
POST /api/v1/career/analyze

{
  "resume_id": "resume_abc123",
  "target_position": "AI Agent 开发实习生",
  "job_description": "./uploads/jd_abc123def456.png",  # 使用图片路径
  "jd_type": "image"  # 图片类型
}
```

系统会自动调用千问的视觉能力解析图片中的 JD 内容。

### 方式 3：上传 JD PDF

**第一步：上传 JD PDF**

```bash
POST /api/v1/jd/upload-pdf

Content-Type: multipart/form-data
file: <JD PDF 文件>
```

**第二步：使用 PDF 路径进行分析**

```bash
POST /api/v1/career/analyze

{
  "resume_id": "resume_abc123",
  "target_position": "AI Agent 开发实习生",
  "job_description": "./uploads/jd_abc123def456.pdf",  # 使用 PDF 路径
  "jd_type": "pdf"  # PDF 类型
}
```

---

## JD 解析结果示例

无论是文本、PDF 还是图片，JD 解析的输出格式都是统一的：

```json
{
  "jd_title": "AI Agent 开发实习生",
  "company": "某某科技公司",
  "core_skills": [
    {
      "skill_name": "Python",
      "must_have": true,
      "proficiency_level": "精通",
      "why_critical": "是 Agent 框架开发的主要语言",
      "how_to_evaluate": "让候选人设计和实现一个简单的 Agent"
    },
    {
      "skill_name": "LLM API 集成",
      "must_have": true,
      "proficiency_level": "熟悉",
      "why_critical": "Agent 需要调用 LLM 完成任务",
      "how_to_evaluate": "问候选人是否有过 OpenAI/Claude API 的使用经验"
    }
  ],
  "nice_to_have": [
    {
      "skill_name": "LangChain/LangGraph 框架",
      "priority": 5,
      "reason": "能快速理解我们的技术栈"
    }
  ],
  "key_responsibilities": [
    {
      "responsibility": "参与 Agent 产品的设计和开发",
      "required_skills": ["Python", "系统设计", "LLM API"]
    }
  ],
  "experience_requirement": {
    "years": "1-2年",
    "specific_requirements": "有过实际项目经验（课程设计不算）",
    "red_lines": "没有任何真实编程经验"
  },
  "education_requirement": {
    "minimum": "本科在读",
    "preferred": "计算机相关专业",
    "notes": "其他专业也可考虑，只要技术能力强"
  },
  "market_reality": {
    "difficulty_rating": 7,
    "candidate_pool_quality": "充足但鱼龙混杂",
    "realistic_salary_range": "15k-25k/月"
  }
}
```

---

## 关键技术栈

### LLMClient（多模型支持）

```python
from app.agents.llm import LLMClient

# 文本输入
llm = LLMClient("qwen")
result = await llm.chat(system_prompt, user_message)

# 图片输入（仅限千问）
llm = LLMClient("qwen")
result = await llm.chat_with_image(system_prompt, user_message, image_path)
```

### 支持的模型

- **千问（Qwen）**：`qwen-vl-max-latest`
  - 支持文本对话
  - **支持图片视觉理解** ✨
  - 用于：简历解析、JD 分析

- **DeepSeek**：`deepseek-chat`
  - 用于：Gap 分析、学习路线、面试题

---

## 配置说明

在 `.env` 中配置以下内容：

```env
# 千问 API
QWEN_API_KEY=your_qwen_api_key
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-vl-max-latest

# DeepSeek API
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# 文件上传
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=10485760  # 10MB
ALLOWED_IMAGE_FORMATS=.png,.jpg,.jpeg,.gif,.webp
```

---

## 为什么需要这些改进？

### 问题 1：大模型容易过度夸赞

**解决方案**：使用严厉的角色扮演
- HR 会挑职业发展的问题
- 技术官会指出真实的技能要求
- 技术大牛会看穿包装，只评估真实能力

### 问题 2：候选人众多，平庸者无竞争力

**解决方案**：严格的评估标准
- 明确指出"缺点"而不仅仅是"优势"
- 提出技术"质疑"而不是盲目相信简历
- 直白地说"为什么不邀请面试"

### 问题 3：手工输入 JD 容易出错

**解决方案**：支持图片上传和自动解析
- 支持截图上传（无需手工复制粘贴）
- 支持 PDF（保留原有格式）
- 支持直接文本输入（最快）

---

## 工作流图

```
┌──────────────────────────────────────────────────┐
│                用户上传简历                        │
│              (POST /resume/upload)               │
└──────────────┬───────────────────────────────────┘
               │
               ▼
       ┌──────────────────┐
       │ 选择 JD 输入方式 │
       └────┬─────┬──────┬─┘
         文本│  PDF│ 图片 │
            │     │      │
     ┌──────▼─┐  ┌▼──┐  ┌▼────────┐
     │直接输入 │  │上载│  │上载图片 │
     │JD文本  │  │PDF │  │(新功能) │
     └──┬───┬─┘  └┬──┘  └┬────────┘
        │   │     │      │
        └───┴─────┴──────┘
              │
              ▼
    ┌─────────────────────────┐
    │  JD 分析（技术官视角）    │
    │  (JDAnalyzerAgent)      │
    │  - 千问（支持多种输入）   │
    └──────────┬──────────────┘
               │
               ▼
    ┌──────────────────────────┐
    │  技能差距分析（大牛视角）  │
    │  (GapAnalyzerAgent)      │
    │  - DeepSeek              │
    └──────────┬───────────────┘
               │
               ▼
    ┌──────────────────────────┐
    │  分析结果输出             │
    │  - 匹配分数               │
    │  - 优势/缺陷             │
    │  - 诚实评价              │
    └──────────────────────────┘
```

---

## 示例对比：改进前后

### 改进前的 Gap 分析

```
"这个候选人的技能和岗位需求匹配度很高。他有5年的Python开发经验，
掌握了机器学习的基础知识，这对AI Agent开发会很有帮助。
我建议邀请他面试。"
```

### 改进后的 Gap 分析（技术大牛视角）

```json
{
  "overall_verdict": "不会邀请面试",
  "match_score": 42,
  "critical_gaps": {
    "missing_skills": [
      {
        "skill": "LLM API 集成",
        "required_proficiency": "精通",
        "candidate_proficiency": "没有提及",
        "severity": "严重",
        "can_be_learned": true,
        "why": "这是 Agent 开发的核心，不是可以临时学的东西"
      }
    ]
  },
  "red_flags": [
    {
      "flag": "简历中的'机器学习基础'很模糊",
      "concern": "没有具体的项目、数据集或指标。这是包装",
      "seriousness": "严重"
    },
    {
      "flag": "3年内跳槽5次",
      "concern": "要么技术能力不够稳定，要么职业规划不清楚",
      "seriousness": "中等"
    }
  ],
  "honest_assessment": "这个候选人的 Python 基础不错，但完全没有 LLM/Agent 相关的经验。
简历上的'机器学习'可能只是在某个课程或 Kaggle 竞赛上接触过，不是真正的工程能力。
频繁跳槽也很担心。我不会邀请这个人面试，因为我们没有时间培养新手。
这个职位需要能立即上手做贡献的人。"
}
```

看到区别了吗？改进后的评价**直白、有据、可操作**。

---

## 下一步

1. ✅ JD 图片解析已完成
2. ⏳ 可考虑支持语音输入 JD（用户朗读职位要求）
3. ⏳ 可考虑实时反馈（分析过程中逐步显示结果）
4. ⏳ 可考虑简历与 JD 的实时匹配度预测
