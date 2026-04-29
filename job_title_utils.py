from __future__ import annotations

import re
from typing import Any


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "; ".join(str(item).strip() for item in value if str(item).strip())
    return str(value).strip()


def _skills_list(parsed_resume: dict[str, Any] | None) -> list[str]:
    if not parsed_resume:
        return []

    skills = parsed_resume.get("skills")
    if isinstance(skills, list):
        return [str(skill).strip() for skill in skills if str(skill).strip()]
    if isinstance(skills, str):
        raw = re.split(r"[,;|]+", skills)
        return [item.strip() for item in raw if item.strip()]
    return []


def _first_experience_title(parsed_resume: dict[str, Any] | None) -> str:
    if not parsed_resume:
        return ""

    experience = _stringify(parsed_resume.get("experience"))
    if not experience:
        return ""

    lines = [line.strip() for line in re.split(r"\n|\|", experience) if line.strip()]
    skip_keywords = {
        "tasks",
        "responsibilities",
        "company",
        "workplace",
        "certificate",
        "achievements",
        "award",
        "description",
        "duties",
        "managed",
        "led",
        "provided",
        "supported",
        "worked",
        "assisted",
        "developed",
        "created",
        "implemented",
    }
    responsibility_indicators = {"and", "provide", "support", "manage", "assist", "develop", "work", "create", "implement", "handle"}
    
    for line in lines:
        lowered = line.lower()
        
        if any(keyword in lowered for keyword in skip_keywords):
            continue
        
        if re.search(r"\d{2}/\d{4}|present|\d{4}", lowered):
            continue
        
        if "," in line:
            continue
        
        word_count = len(line.split())
        if word_count > 5:
            continue
        
        if any(indicator in lowered.split() for indicator in responsibility_indicators):
            continue
        
        if 2 <= len(line) <= 50:
            return line

    return ""


def suggest_job_title_from_parsed_resume(parsed_resume: dict[str, Any] | None) -> str:
    from_experience = _first_experience_title(parsed_resume)
    if from_experience:
        return from_experience

    skills = _skills_list(parsed_resume)
    if not skills:
        return ""

    skill_map = {
    "machine learning": "Machine Learning Engineer",
    "deep learning": "Machine Learning Engineer",
    "artificial intelligence": "AI Engineer",

    "fastapi": "Backend Developer",
    "django": "Python Developer",
    "flask": "Python Developer",
    "python": "Python Developer",

    "sql": "Data Analyst",
    "data analysis": "Data Analyst",
    "data analytics": "Data Analyst",
    "excel": "Data Analyst",
    "power bi": "Data Analyst",

    "javascript": "Frontend Developer",
    "typescript": "Frontend Developer",
    "react": "Frontend Developer",
    "html": "Frontend Developer",
    "css": "Frontend Developer",

    "node": "Backend Developer",
    "node.js": "Backend Developer",
    "java": "Java Developer",
    "spring": "Java Developer",
    "c#": "C# Developer",
    "c++": "C++ Developer",
    "php": "PHP Developer",
    "laravel": "PHP Developer",
    }

    normalized_skills = " ".join(skill.lower().strip() for skill in skills)

    for skill_keyword, job_title in skill_map.items():
        if skill_keyword in normalized_skills:
            return job_title

    return f"{skills[0].title()} Specialist"