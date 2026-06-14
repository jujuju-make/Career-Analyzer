"""GitHub 项目搜索工具 —— 调用 GitHub Search API 按 stars 排序搜索项目"""

import httpx
from typing import List, Dict, Any, Optional


async def search_github_projects(
    query: str,
    per_page: int = 5,
    sort: str = "stars",
    order: str = "desc",
) -> List[Dict[str, Any]]:
    """
    搜索 GitHub 项目，按 stars 数排序

    :param query: 搜索关键词（支持 GitHub 搜索语法，如 "topic:python topic:fastapi"）
    :param per_page: 每页返回数量（默认 5）
    :param sort: 排序方式（默认 stars）
    :param order: 排序方向（默认 desc）
    :return: 项目列表，每个项目包含 name、url、description、stars、forks、language、topics、updated_at
    """
    url = "https://api.github.com/search/repositories"
    params = {
        "q": query,
        "sort": sort,
        "order": order,
        "per_page": per_page,
    }
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Career-Agent/1.0",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()

            projects = []
            for item in data.get("items", []):
                projects.append({
                    "name": item.get("full_name", ""),
                    "url": item.get("html_url", ""),
                    "description": item.get("description", "") or "",
                    "stars": item.get("stargazers_count", 0),
                    "forks": item.get("forks_count", 0),
                    "language": item.get("language") or "",
                    "topics": item.get("topics", []) or [],
                    "updated_at": item.get("updated_at", ""),
                })
            return projects

        except httpx.HTTPStatusError as e:
            print(f"[GitHub Search Tool Error] {e.response.status_code}: {e.response.text}")
            return []
        except Exception as e:
            print(f"[GitHub Search Tool Error] {e}")
            return []


async def search_github_projects_by_skills(
    skills: List[str],
    max_results: int = 3,
) -> List[Dict[str, Any]]:
    """
    根据技能列表搜索 GitHub 项目，自动组合关键词并去重排序

    :param skills: 技能关键词列表
    :param max_results: 最大返回数量（默认 3）
    :return: 按 stars 排序的项目列表
    """
    all_projects = []
    seen = set()

    for skill in skills:
        projects = await search_github_projects(skill, per_page=5)
        for p in projects:
            name = p.get("name", "")
            if name and name not in seen:
                seen.add(name)
                all_projects.append(p)

    # 按 stars 降序排序
    all_projects.sort(key=lambda x: x.get("stars", 0), reverse=True)
    return all_projects[:max_results]
