from job_title_utils import suggest_job_title_from_parsed_resume


def test_python_skill_maps_to_python_developer():
    parsed = {"skills": ["Python", "SQL"], "experience": None}
    assert suggest_job_title_from_parsed_resume(parsed) == "Python Developer"


def test_partial_python_skill_maps_to_python_developer():
    parsed = {"skills": ["Python programming", "SQL"], "experience": None}
    assert suggest_job_title_from_parsed_resume(parsed) == "Python Developer"


def test_experience_title_has_priority_over_skills():
    parsed = {
        "experience": "Senior Data Analyst\nWorked on reporting",
        "skills": ["Python"],
    }
    assert suggest_job_title_from_parsed_resume(parsed) == "Senior Data Analyst"


def test_react_skill_maps_to_frontend_developer():
    parsed = {"skills": ["React", "JavaScript", "HTML"], "experience": ""}
    assert suggest_job_title_from_parsed_resume(parsed) == "Frontend Developer"


def test_machine_learning_skill_maps_to_ml_engineer():
    parsed = {"skills": ["Machine Learning", "Python"], "experience": ""}
    assert suggest_job_title_from_parsed_resume(parsed) == "Machine Learning Engineer"


def test_fastapi_skill_maps_to_backend_developer():
    parsed = {"skills": ["FastAPI", "PostgreSQL"], "experience": ""}
    assert suggest_job_title_from_parsed_resume(parsed) == "Backend Developer"


def test_unknown_skill_falls_back_to_specialist():
    parsed = {"skills": ["Figma"], "experience": ""}
    assert suggest_job_title_from_parsed_resume(parsed) == "Figma Specialist"


def test_empty_resume_returns_empty_string():
    assert suggest_job_title_from_parsed_resume(None) == ""
    
def test_multiple_skills_prioritize_ml_over_python():
    parsed = {"skills": ["Python", "Machine Learning", "SQL"], "experience": ""}
    assert suggest_job_title_from_parsed_resume(parsed) == "Machine Learning Engineer"
    
def test_no_skills_no_experience_returns_empty():
    parsed = {"skills": [], "experience": ""}
    assert suggest_job_title_from_parsed_resume(parsed) == ""
    