# AI Career Agent API Documentation

## 项目简介

AI Career Agent 是一个面向求职者的智能职业规划系统。

用户上传简历和目标岗位 JD 后，系统自动完成：

* 简历解析
* 岗位需求分析
* 技能差距分析（Gap Analysis）
* 个性化学习路线生成
* 面试题生成
* 项目推荐

帮助用户制定更高效的求职准备方案。

---

# 1. 用户上传简历

## POST /api/v1/resume/upload

### Description

上传用户简历 PDF 文件。

### Request

multipart/form-data

| 参数   | 类型  | 必填 |
| ---- | --- | -- |
| file | PDF | 是  |

### Response

```json
{
  "resume_id": "resume_xxx",
  "status": "success"
}
```

---

# 2. 创建求职分析任务

## POST /api/v1/career/analyze

### Description

上传岗位 JD 并开始分析。

### Request

```json
{
  "resume_id": "resume_xxx",
  "target_position": "AI Agent开发实习生",
  "job_description": "岗位描述内容..."
}
```

### Response

```json
{
  "task_id": "task_xxx",
  "status": "processing"
}
```

---

# 3. 获取分析结果

## GET /api/v1/career/result/{task_id}

### Description

返回职业分析结果。

### Response

```json
{
  "match_score": 72,
  "strengths": [
    "FastAPI",
    "RAG",
    "Python"
  ],
  "missing_skills": [
    "Redis",
    "Docker",
    "LangGraph"
  ],
  "summary": "当前已具备 AI 应用开发基础..."
}
```

---

# 4. 生成学习路线

## POST /api/v1/career/roadmap

### Description

根据能力差距生成学习路线。

### Request

```json
{
  "task_id": "task_xxx"
}
```

### Response

```json
{
  "roadmap": [
    {
      "week": 1,
      "topic": "Redis基础"
    },
    {
      "week": 2,
      "topic": "Docker部署"
    },
    {
      "week": 3,
      "topic": "Tool Calling"
    }
  ]
}
```

---

# 5. 生成面试题

## POST /api/v1/interview/generate

### Description

根据岗位要求自动生成面试题。

### Request

```json
{
  "task_id": "task_xxx"
}
```

### Response

```json
{
  "questions": [
    {
      "type": "Python",
      "question": "list和tuple有什么区别？"
    },
    {
      "type": "FastAPI",
      "question": "Pydantic有什么作用？"
    }
  ]
}
```

---

# 6. 项目推荐

## POST /api/v1/project/recommend

### Description

根据技能缺口推荐项目。

### Request

```json
{
  "task_id": "task_xxx"
}
```

### Response

```json
{
  "projects": [
    {
      "title": "AI Career Agent",
      "reason": "同时覆盖Redis、Tool Calling、Prompt Engineering"
    }
  ]
}
```

---

# Agent Workflow

用户上传简历

↓

简历解析 Agent

↓

JD 分析 Agent

↓

技能差距分析 Agent

↓

学习规划 Agent

↓

面试准备 Agent

↓

生成最终职业发展报告

---

# 技术栈

Backend

* FastAPI
* SQLAlchemy
* PostgreSQL
* Redis

LLM

* OpenAI
* Claude
* DeepSeek

AI Framework

* LangChain
* LangGraph（V2）

Deployment

* Docker
* Tencent Cloud

Frontend

* React
* Next.js
