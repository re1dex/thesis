from __future__ import annotations

import html
import io
import json
import os
import re
import hashlib
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from secrets import compare_digest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st

try:
    from SimpleJobHunter import search_google_jobs

    JOB_HUNTER_AVAILABLE = True
except Exception:
    search_google_jobs = None
    JOB_HUNTER_AVAILABLE = False

from config import ALLOWED_UPLOAD_TYPES, APP_TITLE, DEFAULT_OUTPUT_FILENAME, MAX_UPLOAD_SIZE_MB
from job_title_utils import suggest_job_title_from_parsed_resume
from read_pdf_csv import extract_resume_data, extract_text_from_pdf_bytes


DATA_STORE_PATH = Path(__file__).resolve().with_name("dashboard_store.json")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).resolve().with_name("app.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

st.set_page_config(page_title=APP_TITLE, page_icon="📄", layout="wide")


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&display=swap');

        :root {
            color-scheme: light !important;
        }

        html, body, [class*="css"], .stApp {
            font-family: 'Manrope', sans-serif;
            background: radial-gradient(circle at top right, #bfe9ff 0%, #d9f2ff 38%, #edf8ff 100%);
        }

        .main .block-container {
            background: transparent;
        }

        .hero {
            background: linear-gradient(120deg, #0f4c5c 0%, #1f7a8c 100%);
            border-radius: 18px;
            padding: 1.2rem 1.4rem;
            color: #eef6f8;
            margin-bottom: 0.8rem;
            box-shadow: 0 10px 30px rgba(15, 76, 92, 0.22);
        }

        .hero h1 {
            margin: 0;
            font-size: 1.9rem;
            font-weight: 800;
            letter-spacing: 0.2px;
        }

        .hero p {
            margin: 0.35rem 0 0;
            font-size: 1rem;
            opacity: 0.95;
        }

        .pill {
            display: inline-block;
            margin-top: 0.8rem;
            padding: 0.28rem 0.65rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.2);
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.2px;
        }

        .stat-card {
            border-radius: 14px;
            background: #ffffff;
            border: 1px solid #d7e4e7;
            padding: 0.85rem 0.95rem;
            box-shadow: 0 6px 16px rgba(7, 41, 50, 0.07);
        }

        .stat-label {
            font-size: 0.78rem;
            color: #4f6d75;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.4px;
        }

        .stat-value {
            font-size: 1.55rem;
            color: #12343b;
            margin-top: 0.15rem;
            font-weight: 800;
        }

        .section-title {
            color: #0f4c5c;
            font-size: 1.05rem;
            font-weight: 800;
            letter-spacing: 0.2px;
            margin: 0.25rem 0 0.65rem;
        }

        .field-card {
            border-radius: 12px;
            border: 1px solid #dbe5e8;
            background: #ffffff;
            padding: 0.7rem 0.8rem;
            margin-bottom: 0.55rem;
        }

        .field-name {
            color: #48666d;
            font-size: 0.8rem;
            font-weight: 700;
            margin-bottom: 0.2rem;
            text-transform: uppercase;
            letter-spacing: 0.35px;
        }

        .field-value {
            color: #14353c;
            font-size: 0.95rem;
            line-height: 1.35;
            font-weight: 600;
        }

        .badge {
            display: inline-block;
            border-radius: 999px;
            padding: 0.15rem 0.55rem;
            font-size: 0.72rem;
            font-weight: 800;
            margin-left: 0.45rem;
            cursor: help;
        }

        .badge-high { background: #d9f3e6; color: #0a6b44; }
        .badge-medium { background: #fff0c9; color: #8a5d00; }
        .badge-low { background: #ffe1de; color: #9a1e1e; }

        .status-card {
            border-radius: 10px;
            border: 1px solid #1e5f6f;
            background: #d9edf2;
            color: #0f3f4a;
            padding: 0.62rem 0.75rem;
            font-weight: 800;
            margin: 0.4rem 0 0.7rem;
        }

        .helper-note {
            color: #101820;
            font-weight: 800;
            margin: 0.1rem 0 0.6rem;
        }

        .coverage-note {
            color: #102a30;
            font-weight: 800;
            font-size: 0.95rem;
            margin-top: 0.35rem;
        }

        .best-job {
            border-radius: 14px;
            border: 1px solid #0f4c5c;
            background: #f0f7f9;
            padding: 0.9rem;
            margin-bottom: 0.8rem;
        }

        .best-job h4 {
            margin: 0 0 0.35rem;
            color: #0f4c5c;
        }

        .best-job,
        .best-job div,
        .best-job strong {
            color: #12343b;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.4rem;
            background: #e5eef1;
            border-radius: 12px;
            padding: 0.3rem;
            border: 1px solid #c5d8de;
        }

        .stTabs [data-baseweb="tab"] {
            background: #f4f8f9;
            border-radius: 9px;
            color: #34535b;
            font-weight: 700;
            border: 1px solid #d4e2e6;
            padding: 0.35rem 0.9rem;
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(120deg, #0f4c5c 0%, #1f7a8c 100%);
            color: #f4fbfd;
            border-color: #0f4c5c;
        }

        div[data-testid="stFileUploader"] {
            background: #ffffff;
            border: 1px solid #cfe0e5;
            border-radius: 12px;
            padding: 0.45rem 0.55rem;
        }

        div[data-testid="stFileUploaderDropzone"] {
            background: linear-gradient(120deg, #0f4c5c 0%, #1f7a8c 100%) !important;
            border: 2px dashed #d3e9ee !important;
            border-radius: 12px !important;
            color: #f4fbfd !important;
        }

        div[data-testid="stFileUploaderDropzone"] * {
            color: #f4fbfd !important;
            fill: #f4fbfd !important;
            stroke: #f4fbfd !important;
            opacity: 1 !important;
            font-weight: 800 !important;
        }

        div[data-testid="stFileUploaderFile"] {
            background: #eaf2f4 !important;
            border: 1px solid #c1d5db !important;
            border-radius: 10px !important;
        }

        div[data-testid="stFileUploaderFile"] * {
            color: #101820 !important;
            font-weight: 700 !important;
        }

        [data-testid="stWidgetLabel"] p,
        [data-testid="stWidgetLabel"] label,
        .stTextInput label,
        .stTextInput p,
        .stTextInput input,
        .stTextInput input::placeholder,
        .stTextArea textarea,
        .stTextArea textarea::placeholder {
            color: #102a30 !important;
            opacity: 1 !important;
            font-weight: 700 !important;
        }

        .stTextInput input,
        .stTextArea textarea {
            background: #ffffff !important;
            border: 1px solid #b9ced4 !important;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #d7eefb 0%, #edf8ff 100%) !important;
            border-right: 1px solid #9dc7dc !important;
        }

        [data-testid="stSidebar"] * {
            color: #102a30 !important;
        }

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] h4,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] div,
        [data-testid="stSidebar"] li,
        [data-testid="stSidebar"] small,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] * {
            color: #102a30 !important;
            opacity: 1 !important;
        }

        [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
        [data-testid="stSidebar"] label {
            font-weight: 800 !important;
            opacity: 1 !important;
        }

        [data-testid="stSidebar"] input,
        [data-testid="stSidebar"] textarea,
        [data-testid="stSidebar"] select {
            background: #ffffff !important;
            color: #102a30 !important;
            border: 1px solid #b9ced4 !important;
        }

        [data-testid="stSidebar"] [data-baseweb="select"] *,
        [data-testid="stSidebar"] [data-baseweb="select"] input,
        [data-testid="stSidebar"] [data-baseweb="select"] span,
        [data-testid="stSidebar"] [data-baseweb="select"] div {
            color: #102a30 !important;
            opacity: 1 !important;
        }

        [data-testid="stSidebar"] [data-baseweb="select"] > div {
            background: #ffffff !important;
            border: 1px solid #b9ced4 !important;
        }

        [data-testid="stSidebar"] [role="radiogroup"] label,
        [data-testid="stSidebar"] [data-baseweb="radio"] label,
        [data-testid="stSidebar"] [data-baseweb="radio"] span {
            color: #102a30 !important;
            font-weight: 700 !important;
            opacity: 1 !important;
        }

        [data-testid="stSidebar"] button,
        [data-testid="stSidebar"] button * {
            color: #ffffff !important;
            font-weight: 700 !important;
        }

        /* Global button accessibility: enforce visible fill/text for all actions */
        .stButton > button,
        button[kind="primary"],
        [data-testid="baseButton-secondary"],
        [data-testid="baseButton-primary"] {
            background: #0f4c5c !important;
            color: #ffffff !important;
            border: 1px solid #0c3d49 !important;
            border-radius: 10px !important;
            font-weight: 800 !important;
            opacity: 1 !important;
        }

        .stButton > button:hover,
        button[kind="primary"]:hover,
        [data-testid="baseButton-secondary"]:hover,
        [data-testid="baseButton-primary"]:hover {
            background: #0c3d49 !important;
            color: #ffffff !important;
            border-color: #092f39 !important;
        }

        .stButton > button:disabled {
            background: #7ea5b2 !important;
            color: #f5fbfd !important;
            border-color: #6f97a4 !important;
        }

        div[data-testid="stProgress"] p,
        div[data-testid="stProgress"] span {
            color: #102a30 !important;
            font-weight: 800 !important;
            opacity: 1 !important;
        }

        div[data-testid="stSpinner"] *,
        div[data-testid="stSpinner"] p,
        div[data-testid="stSpinner"] span {
            color: #102a30 !important;
            font-weight: 800 !important;
            opacity: 1 !important;
        }
        
        /* Fix only normal Streamlit form/text inputs */
        [data-testid="stTextInput"] label,
        [data-testid="stTextArea"] label,
        [data-testid="stSelectbox"] label,
        [data-testid="stFileUploader"] label,
        [data-testid="stMarkdownContainer"] p {
            color: #102a30 !important;
        }

        /* Fix typed input text */
        .stTextInput input,
        .stTextArea textarea {
            color: #102a30 !important;
            background-color: #ffffff !important;
        }

        /* Keep buttons readable */
        .stButton button,
        .stButton button * {
            color: #ffffff !important;
        }

        /* Keep buttons readable */
        .stButton button,
        .stButton button * {
            color: #ffffff !important;
        }

        /* Keep hero text white */
        .hero,
        .hero * {
            color: #eef6f8 !important;
        }

        /* Keep ONLY selected tab text white */
        .stTabs [data-baseweb="tab"][aria-selected="true"],
        .stTabs [data-baseweb="tab"][aria-selected="true"] * {
            color: #ffffff !important;
        }

        /* Fix dataframe/table text */
        [data-testid="stDataFrame"] *,
        [data-testid="stTable"] * {
            color: #102a30 !important;
        }
        
        /* Recruiter panel text fix */
        .recruiter-panel,
        .recruiter-panel *,
        .recruiter-panel p,
        .recruiter-panel span,
        .recruiter-panel div,
        .recruiter-panel h1,
        .recruiter-panel h2,
        .recruiter-panel h3 {
            color: #102a30 !important;
            opacity: 1 !important;
        }
        
        /* Recruiter panel titles */
        .recruiter-panel h1,
        .recruiter-panel h2 {
            color: #102a30 !important;
            opacity: 1 !important;
        }

        .recruiter-panel h1 {
            font-size: 2.2rem;
            font-weight: 800;
            margin-bottom: 1rem;
        }

        .recruiter-panel h2 {
            font-size: 1.35rem;
            font-weight: 800;
            margin-bottom: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _default_store() -> dict[str, Any]:
    return {
        "admin": {"serpapi_api_key": ""},
        "users": {},
    }


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _load_store() -> dict[str, Any]:
    if not DATA_STORE_PATH.exists():
        logger.info("Store file not found, creating new")
        return _default_store()

    try:
        content = json.loads(DATA_STORE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        logger.error(f"Store file corrupted: {e}. Creating backup and new store.")
        backup_path = DATA_STORE_PATH.with_suffix('.json.backup')
        try:
            DATA_STORE_PATH.rename(backup_path)
            logger.info(f"Created backup at {backup_path}")
        except Exception:
            pass
        return _default_store()
    except Exception as e:
        logger.error(f"Error loading store: {e}")
        return _default_store()

    if not isinstance(content, dict):
        return _default_store()

    content.setdefault("admin", {})
    content["admin"].setdefault("serpapi_api_key", "")
    content.setdefault("users", {})
    for _, user_rec in content["users"].items():
        if isinstance(user_rec, dict):
            _ensure_user_store_fields(user_rec)
            if not user_rec.get("contact") and user_rec.get("parsed_resume"):
                parsed_resume = user_rec.get("parsed_resume")
                if isinstance(parsed_resume, dict):
                    email = _stringify(parsed_resume.get("email", ""))
                    phone = _stringify(parsed_resume.get("phone", ""))
                    if email:
                        user_rec["contact"] = email
                    elif phone:
                        user_rec["contact"] = phone
    return content



def _save_store(store_data: dict[str, Any]) -> None:
    DATA_STORE_PATH.write_text(
        json.dumps(store_data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", _stringify(value).lower()).strip()


def _job_title_matches_query(job_title: Any, query: Any) -> bool:
    normalized_title = _normalize_text(job_title)
    normalized_query = _normalize_text(query)
    if not normalized_title or not normalized_query:
        return False

    if normalized_query in normalized_title or normalized_title in normalized_query:
        return True

    query_tokens = [token for token in normalized_query.split() if len(token) >= 3]
    if not query_tokens:
        return False

    title_tokens = set(normalized_title.split())
    return all(token in title_tokens for token in query_tokens)


def _ensure_user_store_fields(user_rec: dict[str, Any]) -> None:
    user_rec.setdefault("password_hash", "")
    user_rec.setdefault("created_at", "")
    user_rec.setdefault("contact", "")
    user_rec.setdefault("parsed_resume", None)
    user_rec.setdefault("extracted_text", "")
    user_rec.setdefault("parsed_file_name", "")
    user_rec.setdefault("last_job_title", "")
    user_rec.setdefault("jobs_rows", [])
    user_rec.setdefault("matched_jobs", [])
    user_rec.setdefault("parsed_history", [])


def _append_matched_jobs(user_rec: dict[str, Any], search_query: str, jobs_df: pd.DataFrame) -> None:
    matched_jobs = user_rec.setdefault("matched_jobs", [])
    existing_keys = {
        (
            _normalize_text(job.get("job_title")),
            _normalize_text(job.get("company")),
            _normalize_text(job.get("location")),
        )
        for job in matched_jobs
        if isinstance(job, dict)
    }

    for _, row in jobs_df.iterrows():
        job_title = _stringify(row.get("job_title"))
        company = _stringify(row.get("company"))
        location = _stringify(row.get("location"))
        key = (_normalize_text(job_title), _normalize_text(company), _normalize_text(location))
        if key in existing_keys or not job_title:
            continue

        matched_jobs.append(
            {
                "job_title": job_title,
                "company": company,
                "location": location,
                "search_query": search_query,
                "matched_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            }
        )
        existing_keys.add(key)

    if len(matched_jobs) > 100:
        user_rec["matched_jobs"] = matched_jobs[-100:]


def _find_recruiter_matches(store_data: dict[str, Any], query: str) -> list[dict[str, Any]]:
    normalized_query = _normalize_text(query)
    if not normalized_query:
        return []

    matches: list[dict[str, Any]] = []
    for username, user_rec in store_data.get("users", {}).items():
        if not isinstance(user_rec, dict):
            continue

        matched_titles: list[str] = []
        seen_titles: set[str] = set()

        title_sources: list[Any] = []
        title_sources.extend(user_rec.get("matched_jobs", []) or [])
        title_sources.extend(user_rec.get("jobs_rows", []) or [])

        for job in title_sources:
            if not isinstance(job, dict):
                continue
            job_title = _stringify(job.get("job_title") or job.get("title"))
            if job_title and _job_title_matches_query(job_title, normalized_query):
                normalized_title = _normalize_text(job_title)
                if normalized_title not in seen_titles:
                    matched_titles.append(job_title)
                    seen_titles.add(normalized_title)

        legacy_title = _stringify(user_rec.get("last_job_title"))
        if legacy_title and _job_title_matches_query(legacy_title, normalized_query):
            normalized_title = _normalize_text(legacy_title)
            if normalized_title not in seen_titles:
                matched_titles.append(legacy_title)
                seen_titles.add(normalized_title)

        if matched_titles:
            matches.append(
                {
                    "username": username,
                    "contact": _stringify(user_rec.get("contact")) or "-",
                    "matched_titles": matched_titles,
                }
            )

    return matches

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


def _suggest_job_title(parsed_resume: dict[str, Any] | None) -> str:
    return suggest_job_title_from_parsed_resume(parsed_resume)


def _field_confidence(field_name: str, field_value: Any) -> str:
    value = _stringify(field_value)
    if not value:
        return "Low"

    if field_name in {"email", "phone", "linkedin"}:
        return "High" if len(value) >= 8 else "Medium"
    if field_name in {"name", "surname", "full_name"}:
        return "High" if 2 <= len(value.split()) <= 4 else "Medium"
    if field_name in {"skills", "education", "experience", "address"}:
        return "High" if len(value) > 20 else "Medium"
    return "Medium"


def _confidence_tooltip(field_name: str, level: str) -> str:
    return (
        f"Confidence for '{field_name}'. "
        f"{level} means extraction looked {'strong' if level == 'High' else 'usable' if level == 'Medium' else 'uncertain'} "
        "based on formatting and pattern checks."
    )


def _confidence_badge(level: str, field_name: str) -> str:
    css_class = {
        "High": "badge badge-high",
        "Medium": "badge badge-medium",
        "Low": "badge badge-low",
    }.get(level, "badge badge-medium")
    tooltip = html.escape(_confidence_tooltip(field_name, level), quote=True)
    return f'<span class="{css_class}" title="{tooltip}">{level} ⓘ</span>'


def _rank_jobs(jobs_df: pd.DataFrame, parsed_resume: dict[str, Any] | None) -> pd.DataFrame:
    ranked_df = jobs_df.copy()
    skills = [skill.lower() for skill in _skills_list(parsed_resume)]

    rankings: list[int] = []
    matched_skills: list[str] = []
    rank_confidence: list[str] = []

    for _, row in ranked_df.iterrows():
        description = _stringify(row.get("description", "")).lower()
        if not description:
            rankings.append(0)
            matched_skills.append("")
            rank_confidence.append("Low")
            continue

        found = [skill for skill in skills if skill and skill in description]
        score = len(found)
        rankings.append(score)
        matched_skills.append(", ".join(found[:8]))
        if score >= 5:
            rank_confidence.append("High")
        elif score >= 2:
            rank_confidence.append("Medium")
        else:
            rank_confidence.append("Low")

    ranked_df.insert(0, "Ranking", rankings)
    ranked_df.insert(1, "Ranking Confidence", rank_confidence)
    ranked_df.insert(2, "Matched Skills", matched_skills)
    ranked_df = ranked_df.sort_values(by=["Ranking", "company"], ascending=[False, True]).reset_index(drop=True)
    return ranked_df


def _reset_view(clear_upload: bool = True) -> None:
    st.session_state.parsed_resume = None
    st.session_state.extracted_text = ""
    st.session_state.parsed_file_name = ""
    st.session_state.jobs_df = None
    st.session_state.job_error = ""
    st.session_state.job_title_input = ""
    if clear_upload:
        st.session_state.uploader_nonce = st.session_state.get("uploader_nonce", 0) + 1


def _load_user_into_session(username: str, store: dict[str, Any]) -> None:
    user_data = store["users"].get(username, {})
    st.session_state.current_user = username
    st.session_state.parsed_resume = user_data.get("parsed_resume")
    st.session_state.extracted_text = user_data.get("extracted_text", "")
    st.session_state.parsed_file_name = user_data.get("parsed_file_name", "")
    st.session_state.job_title_input = user_data.get("last_job_title", "")
    jobs_rows = user_data.get("jobs_rows") or []
    st.session_state.jobs_df = pd.DataFrame(jobs_rows) if jobs_rows else None
    st.session_state.job_error = ""
    st.session_state.selected_history_index = 0


def _clear_access_control_inputs() -> None:
    for key in [
        "admin_password_input",
        "user_auth_action",
        "username_input",
        "user_password_input",
        "confirm_password_input",
    ]:
        if key in st.session_state:
            del st.session_state[key]


def _set_active_user_query_param(username: str) -> None:
    st.query_params["user"] = username


def _clear_active_user_query_param() -> None:
    if "user" in st.query_params:
        del st.query_params["user"]


def _restore_active_user_from_query_param(store: dict[str, Any]) -> None:
    if st.session_state.current_user:
        return

    query_user = st.query_params.get("user", "")
    if not isinstance(query_user, str):
        return

    username = query_user.strip()
    if username and username in store.get("users", {}):
        _load_user_into_session(username, store)


_inject_styles()

store = _load_store()

if "uploader_nonce" not in st.session_state:
    st.session_state.uploader_nonce = 0
if "current_user" not in st.session_state:
    st.session_state.current_user = ""
if "admin_ok" not in st.session_state:
    st.session_state.admin_ok = False
if "recruiter_ok" not in st.session_state:
    st.session_state.recruiter_ok = False
if "parsed_resume" not in st.session_state:
    st.session_state.parsed_resume = None
if "extracted_text" not in st.session_state:
    st.session_state.extracted_text = ""
if "parsed_file_name" not in st.session_state:
    st.session_state.parsed_file_name = ""
if "job_title_input" not in st.session_state:
    st.session_state.job_title_input = ""
if "jobs_df" not in st.session_state:
    st.session_state.jobs_df = None
if "job_error" not in st.session_state:
    st.session_state.job_error = ""
if "last_mode" not in st.session_state:
    st.session_state.last_mode = "User"
if "selected_history_index" not in st.session_state:
    st.session_state.selected_history_index = 0
if "access_mode" not in st.session_state:
    st.session_state.access_mode = "User"
if "login_attempts" not in st.session_state:
    st.session_state.login_attempts = {}  

st.markdown(
    """
    <div class="hero">
            <h1>Automated Job Market Scout</h1>
            <p>We are finding the best matching jobs from your CV skillset.</p>
      <span class="pill">Dashboard View</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown("## Access Control")
mode = st.sidebar.radio("Mode", ["User", "Admin", "Recruiter"], horizontal=True, key="access_mode")

if st.session_state.last_mode != mode:
    _clear_access_control_inputs()
    has_active_session = bool(st.session_state.current_user) or bool(st.session_state.admin_ok) or bool(st.session_state.recruiter_ok)
    if mode == "User" and has_active_session:
        st.session_state.current_user = ""
        st.session_state.admin_ok = False
        st.session_state.recruiter_ok = False
        _clear_active_user_query_param()
        _reset_view(clear_upload=False)
st.session_state.last_mode = mode

if mode == "Admin":
    st.sidebar.markdown("### Admin Login")
    admin_password = st.sidebar.text_input("Admin password", type="password", key="admin_password_input")
    if st.sidebar.button("Login as Admin"):
        expected_password = os.environ.get("APP_ADMIN_PASSWORD", "admin123").strip()
        if not compare_digest(admin_password, expected_password):
            st.session_state.admin_ok = False
            st.sidebar.error("Invalid admin password.")
            logger.warning("Failed admin login attempt")
        else:
            st.session_state.admin_ok = True
            logger.info("Admin login successful")

    if st.session_state.admin_ok:
        st.sidebar.success("Admin session active.")
        if st.sidebar.button("Logout Admin"):
            st.session_state.admin_ok = False
            st.rerun()

        current_key = store["admin"].get("serpapi_api_key", "")
        updated_key = st.sidebar.text_input("Stored SerpApi key", value=current_key, type="password")
        if st.sidebar.button("Save API key"):
            store["admin"]["serpapi_api_key"] = updated_key.strip()
            _save_store(store)
            st.sidebar.success("SerpApi key saved.")

    st.info("Admin view is for API key management.")
    st.stop()

if mode == "Recruiter":
    st.sidebar.markdown("### Recruiter Login")
    recruiter_password = st.sidebar.text_input("Recruiter password", type="password", key="recruiter_password_input")
    if st.sidebar.button("Login as Recruiter"):
        expected_password = os.environ.get("APP_RECRUITER_PASSWORD", "recruiter123").strip()
        if not compare_digest(recruiter_password, expected_password):
            st.session_state.recruiter_ok = False
            st.sidebar.error("Invalid recruiter password.")
            logger.warning("Failed recruiter login attempt")
        else:
            st.session_state.recruiter_ok = True
            logger.info("Recruiter login successful")

    if st.session_state.get("recruiter_ok"):
        st.sidebar.success("Recruiter session active.")
        if st.sidebar.button("Logout Recruiter"):
            st.session_state.recruiter_ok = False
            st.rerun()

        st.markdown(
            """
            <div class="recruiter-panel">
                <h1>Recruiter Panel</h1>
                <h2>Local Job Match Search</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )
        recruiter_query = st.text_input(
            "Search matched jobs by title",
            placeholder="Enter a job title",
            key="recruiter_job_query",
        )

        if recruiter_query.strip():
            recruiter_matches = _find_recruiter_matches(store, recruiter_query)
            if recruiter_matches:
                st.write(f"Matches found: {len(recruiter_matches)}")
                for match in recruiter_matches:
                    with st.container(border=True):
                        st.markdown(f"**Name:** {match['username']}")
                        st.markdown(f"**Contact:** {match['contact']}")
                        st.markdown(
                            "**Matched job titles:** " + ", ".join(match["matched_titles"])
                        )
            else:
                st.info("No local matches found for that title yet.")
        else:
            st.info("Type a job title to search the locally saved user matches.")
    else:
        st.info("Please login to access the recruiter panel.")
   
    st.stop()


st.sidebar.markdown("### User Login")
auth_action = st.sidebar.radio("User action", ["Login", "Register"], horizontal=True, key="user_auth_action")
username_input = st.sidebar.text_input("Username", value="", key="username_input")
user_password = st.sidebar.text_input("Password", type="password", key="user_password_input")
confirm_password = ""
contact_input = ""
if auth_action == "Register":
    confirm_password = st.sidebar.text_input("Confirm password", type="password", key="confirm_password_input")
    contact_input = st.sidebar.text_input("Contact", key="contact_input")

def _is_username_valid(username: str) -> bool:
    """Validate username format: 3-32 chars, alphanumeric, underscore, hyphen only."""
    return bool(re.match(r'^[a-zA-Z0-9_-]{3,32}$', username))

def _check_rate_limit(username: str, is_login: bool = True) -> tuple[bool, str]:
    return True, ""

if st.sidebar.button(auth_action):
    username_clean = username_input.strip()
    if not username_clean:
        st.sidebar.error("Enter a username.")
    elif not _is_username_valid(username_clean):
        st.sidebar.error("Username must be 3-32 chars: letters, numbers, - or _ only.")
    elif not user_password.strip():
        st.sidebar.error("Enter a password.")
    elif auth_action == "Register" and user_password != confirm_password:
        st.sidebar.error("Passwords do not match.")
    else:
        allowed, msg = _check_rate_limit(username_clean, is_login=(auth_action == "Login"))
        if not allowed:
            st.sidebar.error(msg)
            logger.warning(f"Rate limit exceeded for user: {username_clean}")
        else:
            user_rec = store["users"].get(username_clean)

            if auth_action == "Register":
                if user_rec is not None:
                    st.sidebar.error("User already exists. Please login instead.")
                    logger.warning(f"Registration attempt for existing user: {username_clean}")
                else:
                    store["users"][username_clean] = {
                        "password_hash": _hash_password(user_password),
                        "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                        "contact": contact_input.strip(),
                        "parsed_resume": None,
                        "extracted_text": "",
                        "parsed_file_name": "",
                        "last_job_title": "",
                        "jobs_rows": [],
                        "matched_jobs": [],
                        "parsed_history": [],
                    }
                    _save_store(store)
                    st.sidebar.success("Registration successful. You can now login.")
                    logger.info(f"New user registered: {username_clean}")
            else:
                if user_rec is None:
                    st.sidebar.error("User not found. Please register first.")
                    logger.warning(f"Login attempt for non-existent user: {username_clean}")
                else:
                    stored_hash = user_rec.get("password_hash", "")
                    current_hash = _hash_password(user_password)

                    if not stored_hash:
                        user_rec["password_hash"] = current_hash
                        _save_store(store)
                        stored_hash = current_hash

                    if not compare_digest(stored_hash, current_hash):
                        st.sidebar.error("Wrong password.")
                        logger.warning(f"Failed login for user: {username_clean}")
                    else:
                        _load_user_into_session(username_clean, store)
                        _clear_access_control_inputs()
                        logger.info(f"User login successful: {username_clean}")
                        st.rerun()


def _clear_persisted_user_data(store_data: dict[str, Any], username: str) -> None:
    user_rec = store_data.get("users", {}).get(username)
    if not isinstance(user_rec, dict):
        return

    user_rec["parsed_resume"] = None
    user_rec["extracted_text"] = ""
    user_rec["parsed_file_name"] = ""
    user_rec["last_job_title"] = ""
    user_rec["jobs_rows"] = []
    user_rec["parsed_history"] = []
    _save_store(store_data)


def _validate_parsed_resume(data: Any) -> bool:
    """Validate that parsed_resume has required structure."""
    if not isinstance(data, dict):
        return False
    required_keys = {"file_name", "full_name", "email", "skills"}
    has_at_least_one = any(k in data for k in required_keys)
    return has_at_least_one

def _load_selected_history_entry(store_data: dict[str, Any], username: str, history_index: int) -> None:
    user_rec = store_data.get("users", {}).get(username)
    if not isinstance(user_rec, dict):
        logger.error(f"User record not found for: {username}")
        return

    history_items = user_rec.get("parsed_history") or []
    if history_index < 0 or history_index >= len(history_items):
        logger.error(f"History index {history_index} out of range for user: {username}")
        return

    selected_item = history_items[history_index]
    parsed_resume = selected_item.get("parsed_resume")
    if not _validate_parsed_resume(parsed_resume):
        logger.error(f"Corrupted history entry at index {history_index} for user: {username}")
        return

    st.session_state.parsed_resume = parsed_resume
    st.session_state.extracted_text = selected_item.get("extracted_text", "")
    st.session_state.parsed_file_name = selected_item.get("file_name", "")
    st.session_state.job_title_input = _suggest_job_title(parsed_resume)
    st.session_state.jobs_df = None
    st.session_state.job_error = ""

    user_rec["parsed_resume"] = parsed_resume
    user_rec["extracted_text"] = st.session_state.extracted_text
    user_rec["parsed_file_name"] = st.session_state.parsed_file_name
    user_rec["last_job_title"] = st.session_state.job_title_input
    user_rec["jobs_rows"] = []
    _save_store(store_data)

if not st.session_state.current_user:
    st.markdown(
        '<div class="status-card">Login with a username from the sidebar to continue.</div>',
        unsafe_allow_html=True,
    )
    st.stop()

st.sidebar.success(f"Logged in as: {st.session_state.current_user}")
if st.sidebar.button("Logout User"):
    st.session_state.current_user = ""
    _clear_active_user_query_param()
    _reset_view(clear_upload=True)
    st.rerun()

with st.container(border=True):
    st.markdown('<div class="section-title">Upload CV</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Click to upload CV",
        type=ALLOWED_UPLOAD_TYPES,
        accept_multiple_files=False,
        label_visibility="collapsed",
        key=f"uploader_{st.session_state.uploader_nonce}",
    )

    col_parse, col_reset = st.columns([1, 1])
    parse_clicked = col_parse.button("Parse CV", type="primary", use_container_width=True)
    reset_clicked = col_reset.button("Reset View", use_container_width=True)

if reset_clicked:
    _clear_persisted_user_data(store, st.session_state.current_user)
    _reset_view(clear_upload=True)
    st.rerun()

if uploaded_file is None:
    st.info("No CV selected yet.")
else:
    st.markdown(
        f'<div class="status-card">CV selected: {uploaded_file.name}</div>',
        unsafe_allow_html=True,
    )

    if uploaded_file.size > MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        st.error(
            f"File is too large ({uploaded_file.size / (1024 * 1024):.2f} MB). "
            f"Maximum allowed is {MAX_UPLOAD_SIZE_MB} MB."
        )
    else:
        if parse_clicked:
            try:
                with st.spinner("Parsing CV..."):
                    pdf_bytes = uploaded_file.read()
                    
                    if not pdf_bytes.startswith(b'%PDF'):
                        st.error("❌ File is not a valid PDF. Please upload a PDF file.")
                        logger.warning(f"Non-PDF file upload attempt: {uploaded_file.name}")
                    else:
                        extracted_text = extract_text_from_pdf_bytes(pdf_bytes)
                        parsed_resume = extract_resume_data(extracted_text, file_name=uploaded_file.name)
                        st.session_state.parsed_resume = parsed_resume
                        st.session_state.extracted_text = extracted_text
                        st.session_state.parsed_file_name = uploaded_file.name
                        st.session_state.job_title_input = _suggest_job_title(parsed_resume)
                        st.session_state.jobs_df = None
                        st.session_state.job_error = ""

                        user_rec = store["users"][st.session_state.current_user]
                        user_rec["parsed_resume"] = parsed_resume
                        user_rec["extracted_text"] = extracted_text
                        user_rec["parsed_file_name"] = uploaded_file.name
                        user_rec["last_job_title"] = st.session_state.job_title_input
                        user_rec["jobs_rows"] = []
                        user_rec.setdefault("parsed_history", [])
                        
                        if not user_rec.get("contact"):
                            email = _stringify(parsed_resume.get("email", ""))
                            phone = _stringify(parsed_resume.get("phone", ""))
                            if email:
                                user_rec["contact"] = email
                            elif phone:
                                user_rec["contact"] = phone
                        
                        MAX_HISTORY = 50
                        if len(user_rec["parsed_history"]) >= MAX_HISTORY:
                            user_rec["parsed_history"] = user_rec["parsed_history"][1:]
                        
                        user_rec["parsed_history"].append(
                            {
                                "parsed_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                                "file_name": uploaded_file.name,
                                "fields_extracted": sum(1 for v in parsed_resume.values() if _stringify(v)),
                                "parsed_resume": parsed_resume,
                                "extracted_text": extracted_text,
                            }
                        )
                        _save_store(store)
                        logger.info(f"CV parsed successfully for user: {st.session_state.current_user}")
            except ValueError as e:
                st.error(f"❌ Failed to parse PDF: {str(e)[:100]}")
                logger.error(f"PDF parsing error for user {st.session_state.current_user}: {e}")
            except Exception as e:
                st.error(f"❌ Unexpected error while parsing PDF: {str(e)[:100]}")
                logger.error(f"Unexpected error parsing PDF: {e}", exc_info=True)

if st.session_state.parsed_resume is not None:
    output_row = {
        key: "; ".join(value) if isinstance(value, list) else (value or "")
        for key, value in st.session_state.parsed_resume.items()
    }
    output_df = pd.DataFrame([output_row])

    filled_fields = sum(1 for value in st.session_state.parsed_resume.values() if _stringify(value))
    total_fields = len(st.session_state.parsed_resume)
    confidence_levels = [
        _field_confidence(key, value) for key, value in st.session_state.parsed_resume.items()
    ]
    confidence_points = {"High": 1.0, "Medium": 0.65, "Low": 0.25}
    confidence_avg = round(
        100 * (sum(confidence_points[level] for level in confidence_levels) / max(len(confidence_levels), 1))
    )
    skills_count = len(_skills_list(st.session_state.parsed_resume))

    kpi_1, kpi_2, kpi_3, kpi_4 = st.columns(4)
    kpi_1.markdown(
        f'<div class="stat-card"><div class="stat-label">Fields Extracted</div><div class="stat-value">{filled_fields}/{total_fields}</div></div>',
        unsafe_allow_html=True,
    )
    kpi_2.markdown(
        f'<div class="stat-card"><div class="stat-label">Confidence Avg</div><div class="stat-value">{confidence_avg}%</div></div>',
        unsafe_allow_html=True,
    )
    kpi_3.markdown(
        f'<div class="stat-card"><div class="stat-label">Skills Found</div><div class="stat-value">{skills_count}</div></div>',
        unsafe_allow_html=True,
    )
    jobs_count = 0 if st.session_state.jobs_df is None else len(st.session_state.jobs_df)
    kpi_4.markdown(
        f'<div class="stat-card"><div class="stat-label">Jobs Matched</div><div class="stat-value">{jobs_count}</div></div>',
        unsafe_allow_html=True,
    )

    st.progress(min(confidence_avg, 100), text=f"Parse confidence estimate: {confidence_avg}%")

    tab_overview, tab_fields, tab_text, tab_jobs = st.tabs(
        ["Overview", "Parsed Fields", "Raw Text", "Job Discovery"]
    )

    with tab_overview:
        left_col, right_col = st.columns([1.15, 1])
        with left_col:
            st.markdown('<div class="section-title">Profile Snapshot</div>', unsafe_allow_html=True)
            highlight_keys = [
                "file_name",
                "full_name",
                "email",
                "phone",
                "address",
                "linkedin",
            ]
            for key in highlight_keys:
                value = _stringify(st.session_state.parsed_resume.get(key))
                if not value:
                    continue
                st.markdown(
                    f'<div class="field-card"><div class="field-name">{key.replace("_", " ")}</div><div class="field-value">{value}</div></div>',
                    unsafe_allow_html=True,
                )

        with right_col:
            st.markdown('<div class="section-title">Section Coverage</div>', unsafe_allow_html=True)
            section_values = {
                "education": len(_stringify(st.session_state.parsed_resume.get("education"))),
                "experience": len(_stringify(st.session_state.parsed_resume.get("experience"))),
                "skills": len(_stringify(st.session_state.parsed_resume.get("skills"))),
                "address": len(_stringify(st.session_state.parsed_resume.get("address"))),
            }
            coverage_df = pd.DataFrame(
                {
                    "section": list(section_values.keys()),
                    "length": list(section_values.values()),
                }
            ).set_index("section")
            st.bar_chart(coverage_df)
            st.markdown(
                '<div class="coverage-note">Coverage bars show extracted content length per section. Higher values usually indicate richer extraction.</div>',
                unsafe_allow_html=True,
            )

            st.markdown('<div class="section-title">Parsed CV History</div>', unsafe_allow_html=True)
            current_user_data = store.get("users", {}).get(st.session_state.current_user, {})
            parsed_history = current_user_data.get("parsed_history") or []
            if parsed_history:
                history_options = []
                for item in parsed_history:
                    try:
                        parsed_at = item.get('parsed_at', '-')
                        file_name = item.get('file_name', 'unknown')
                        if parsed_at != '-':
                            dt = datetime.fromisoformat(parsed_at.replace('Z', '+00:00'))
                            friendly_time = dt.strftime("%b %d, %I:%M %p")
                        else:
                            friendly_time = parsed_at
                        history_options.append(f"{friendly_time} | {file_name}")
                    except Exception as e:
                        logger.warning(f"Error formatting history item: {e}")
                        history_options.append(f"{item.get('parsed_at', '-')} | {item.get('file_name', 'unknown')}")
                
                st.session_state.selected_history_index = st.selectbox(
                    "Choose a previously parsed CV",
                    list(range(len(history_options))),
                    format_func=lambda idx: history_options[idx],
                    index=min(st.session_state.selected_history_index, len(history_options) - 1),
                )
                if st.button("Select CV", use_container_width=True):
                    _load_selected_history_entry(store, st.session_state.current_user, st.session_state.selected_history_index)
                    st.rerun()
                st.caption(f"Saved parsed CVs: {len(parsed_history)}")
            else:
                st.info("No previously parsed CVs yet.")

    with tab_fields:
        st.markdown('<div class="section-title">Extracted Fields</div>', unsafe_allow_html=True)

        field_rows = []
        for key, value in st.session_state.parsed_resume.items():
            text_value = _stringify(value)
            confidence = _field_confidence(key, value)
            field_rows.append(
                {
                    "Field": key,
                    "Value": text_value,
                    "Confidence": confidence,
                    "Confidence Info": _confidence_tooltip(key, confidence),
                }
            )

        field_df = pd.DataFrame(field_rows)
        st.dataframe(field_df, use_container_width=True, hide_index=True)

        for _, row in field_df.iterrows():
            value_preview = row["Value"] if row["Value"] else "Not detected"
            badge = _confidence_badge(str(row["Confidence"]), str(row["Field"]))
            st.markdown(
                (
                    f'<div class="field-card"><div class="field-name">{row["Field"]}{badge}</div>'
                    f'<div class="field-value">{value_preview}</div></div>'
                ),
                unsafe_allow_html=True,
            )

        csv_buffer = io.StringIO()
        output_df.to_csv(csv_buffer, index=False)
        st.download_button(
            "Download Parsed CSV",
            data=csv_buffer.getvalue(),
            file_name=DEFAULT_OUTPUT_FILENAME,
            mime="text/csv",
        )

    with tab_text:
        st.markdown('<div class="section-title">Extracted PDF Text</div>', unsafe_allow_html=True)
        if st.session_state.extracted_text.strip():
            st.text_area(
                "Extracted PDF Text",
                st.session_state.extracted_text,
                height=420,
                label_visibility="collapsed",
            )
        else:
            st.warning("No extractable text was found in this PDF.")

    with tab_jobs:
        st.markdown('<div class="section-title">Job Discovery</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="helper-note">Suggested job title is inferred from your experience and skills to support job discovery.</div>',
            unsafe_allow_html=True,
        )

        form_left, form_right = st.columns(2)
        with form_left:
            job_title = st.text_input("Job title", key="job_title_input")
            country_code = (
                st.text_input("Country code", value="us", max_chars=2).lower().strip() or "us"
            )
        with form_right:
            saved_api_key = store.get("admin", {}).get("serpapi_api_key", "")
            if saved_api_key:
                st.markdown('<div class="status-card">Using SerpApi key from admin settings.</div>', unsafe_allow_html=True)
            else:
                st.warning("Admin has not saved a SerpApi key yet.")

        find_clicked = st.button("Discover Jobs", type="primary", use_container_width=True)

        if find_clicked:
            if not JOB_HUNTER_AVAILABLE:
                st.session_state.job_error = (
                    "Job search dependencies are missing. Install: pip install google-search-results ipython"
                )
                st.session_state.jobs_df = None
            elif not job_title:
                st.session_state.job_error = "Please enter a job title before searching."
                st.session_state.jobs_df = None
            elif not saved_api_key:
                st.session_state.job_error = "Admin must save a SerpApi key first."
                st.session_state.jobs_df = None
            else:
                try:
                    with st.spinner("Searching matching jobs..."):
                        jobs_df, raw_results = search_google_jobs(
                            job_title=job_title,
                            limit=10,
                            country=country_code,
                            language="en",
                            api_key=saved_api_key,
                        )

                    if jobs_df.empty:
                        if isinstance(raw_results, dict) and raw_results.get("error"):
                            error_msg = raw_results.get('error')
                            if "API" in error_msg or "key" in error_msg.lower():
                                st.error(f"❌ SerpAPI Error (invalid key?): {error_msg}\nPlease ask admin to update the API key.")
                            else:
                                st.session_state.job_error = f"SerpApi error: {error_msg}"
                        else:
                            st.session_state.job_error = "No jobs found for that title/location."
                        st.session_state.jobs_df = None
                        logger.warning(f"Job search returned no results for: {job_title}")
                    else:
                        ranked = _rank_jobs(jobs_df, st.session_state.parsed_resume)
                        st.session_state.job_error = ""
                        st.session_state.jobs_df = ranked

                        user_rec = store["users"][st.session_state.current_user]
                        user_rec["last_job_title"] = job_title
                        user_rec["jobs_rows"] = ranked.to_dict(orient="records")
                        _append_matched_jobs(user_rec, job_title, ranked)
                        _save_store(store)
                        logger.info(f"Found {len(ranked)} jobs for user {st.session_state.current_user}")
                except Exception as e:
                    st.error(f"❌ Job search failed: {str(e)[:100]}")
                    logger.error(f"Job search error: {e}", exc_info=True)
                    st.session_state.jobs_df = None

        if st.session_state.job_error:
            st.error(st.session_state.job_error)
        elif st.session_state.jobs_df is not None:
            st.markdown(
                (
                    f'<div class="status-card">Found {len(st.session_state.jobs_df)} matching jobs. '
                    "Sorted by ranking (highest first).</div>"
                ),
                unsafe_allow_html=True,
            )

            top_job = st.session_state.jobs_df.iloc[0]
            st.markdown(
                (
                    '<div class="best-job">'
                    '<h4>Top Discovered Job</h4>'
                    f"<div><strong>{html.escape(_stringify(top_job.get('job_title')))}</strong>"
                    f" at {html.escape(_stringify(top_job.get('company')))}</div>"
                    f"<div>Ranking: {int(top_job.get('Ranking', 0))}</div>"
                    f"<div>Matched skills: {html.escape(_stringify(top_job.get('Matched Skills')) or '-')}</div>"
                    "</div>"
                ),
                unsafe_allow_html=True,
            )

            st.dataframe(st.session_state.jobs_df, use_container_width=True)

            jobs_csv = io.StringIO()
            st.session_state.jobs_df.to_csv(jobs_csv, index=False)
            csv_filename = f"{st.session_state.job_title_input.lower().replace(' ', '_')}_jobs.csv"
            st.download_button(
                "Download Discovered Jobs CSV",
                data=jobs_csv.getvalue(),
                file_name=csv_filename,
                mime="text/csv",
            )
