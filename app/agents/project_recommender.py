"""项目推荐 Agent —— 根据 JD 需求从 GitHub 推荐实战项目"""

from typing import List, Dict, Any
from app.agents.base import BaseAgent
from app.tools.github_search import search_github_projects_by_skills


class ProjectRecommenderAgent(BaseAgent):
    """根据 JD 分析结果，从 GitHub 搜索推荐实战项目"""

    async def run(self, jd_analysis: dict) -> List[Dict[str, Any]]:
        """
        根据 JD 分析结果推荐 3 个 GitHub 项目

        :param jd_analysis: JD 分析结果（含 core_skills 等）
        :return: 3 个 star 数最多的推荐项目列表
        """
        # 从 JD 分析中提取技能关键词
        skills = self._extract_skills(jd_analysis)

        # 调用工具按技能搜索 GitHub 项目，取 star 数最多的 3 个
        top_projects = await search_github_projects_by_skills(skills, max_results=3)

        return top_projects

    def _extract_skills(self, jd_analysis: dict) -> List[str]:
        """从 JD 分析结果中提取技能关键词"""
        skills = []

        # 从 core_skills 提取
        core_skills = jd_analysis.get("core_skills", []) or []
        for skill in core_skills:
            if isinstance(skill, dict):
                name = skill.get("skill_name", "")
                if name:
                    skills.append(name)

        # 从 nice_to_have 提取
        nice_to_have = jd_analysis.get("nice_to_have", []) or []
        for skill in nice_to_have:
            if isinstance(skill, dict):
                name = skill.get("skill_name", "")
                if name:
                    skills.append(name)

        return skills
