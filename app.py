from __future__ import annotations

import io
import os
from typing import Any

import pandas as pd
import streamlit as st

try:
    from SimpleJobHunter import search_google_jobs

    JOB_HUNTER_AVAILABLE = True
except Exception:
    search_google_jobs = None
    JOB_HUNTER_AVAILABLE = False
from config import (
    ALLOWED_UPLOAD_TYPES,
    APP_TITLE,
    DEFAULT_OUTPUT_FILENAME,
    MAX_UPLOAD_SIZE_MB,
)
from read_pdf_csv import extract_resume_data, extract_text_from_pdf_bytes


st.set_page_config(page_title=APP_TITLE, page_icon="📄", layout="wide")


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&display=swap');

        html, body, [class*="css"], .stApp {
            font-family: 'Manrope', sans-serif;
            background: radial-gradient(circle at top right, #d7efe8 0%, #f3f5f6 42%, #f8faf9 100%);
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

        div[data-testid="stFileUploaderDropzone"] [data-testid="stFileUploaderDropzoneInstructions"] span {
            color: #f4fbfd !important;
            font-weight: 800 !important;
        }

        div[data-testid="stFileUploaderDropzone"] [data-testid="stFileUploaderDropzoneInstructions"] small {
            color: #e7f4f8 !important;
            font-weight: 700 !important;
        }

        div[data-testid="stFileUploaderDropzone"] [data-testid="stFileUploaderDropzoneInstructions"] a,
        div[data-testid="stFileUploaderDropzone"] [data-testid="stFileUploaderDropzoneInstructions"] button,
        div[data-testid="stFileUploaderDropzone"] [data-testid="stFileUploaderDropzoneInstructions"] p,
        div[data-testid="stFileUploaderDropzone"] [data-testid="stFileUploaderDropzoneInstructions"] * {
            color: #f4fbfd !important;
            opacity: 1 !important;
            font-weight: 800 !important;
        }

        /* Fallback for Streamlit versions with different uploader DOM */
        div[data-testid="stFileUploaderDropzone"] * {
            color: #f4fbfd !important;
            fill: #f4fbfd !important;
            stroke: #f4fbfd !important;
            opacity: 1 !important;
        }

        div[data-testid="stFileUploader"] p,
        div[data-testid="stFileUploader"] span,
        div[data-testid="stFileUploader"] label {
            color: #f4fbfd !important;
        }

        div[data-testid="stFileUploaderFile"] {
            background: #eaf2f4 !important;
            border: 1px solid #c1d5db !important;
            border-radius: 10px !important;
        }

        div[data-testid="stFileUploaderFile"] *,
        div[data-testid="stFileUploaderFileName"],
        div[data-testid="stFileUploaderFileData"] {
            color: #101820 !important;
            font-weight: 700 !important;
        }

        div[data-testid="stFileUploader"] small {
            color: #45656d !important;
            font-weight: 600;
        }

        /* Force high-contrast labels/help text in form controls */
        [data-testid="stWidgetLabel"] p,
        [data-testid="stWidgetLabel"] span,
        .stTextInput label,
        .stTextInput p,
        .stCaption,
        .stCaption p {
            color: #12343b !important;
            font-weight: 700 !important;
        }

        div[data-testid="stProgress"] p,
        div[data-testid="stProgress"] span {
            color: #101820 !important;
            font-weight: 800 !important;
            opacity: 1 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "; ".join(str(item).strip() for item in value if str(item).strip())
    return str(value).strip()


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


def _confidence_badge(level: str) -> str:
    css_class = {
        "High": "badge badge-high",
        "Medium": "badge badge-medium",
        "Low": "badge badge-low",
    }.get(level, "badge badge-medium")
    return f"<span class=\"{css_class}\">{level}</span>"


_inject_styles()

st.markdown(
    """
    <div class="hero">
      <h1>CV Intelligence Dashboard</h1>
      <p>Parse resumes, inspect extracted fields, and discover matching jobs in one elegant workflow.</p>
      <span class="pill">Thesis Demo View</span>
    </div>
    """,
    unsafe_allow_html=True,
)

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

with st.container(border=True):
    st.markdown('<div class="section-title">Upload</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Click to upload CV",
        type=ALLOWED_UPLOAD_TYPES,
        accept_multiple_files=False,
        label_visibility="collapsed",
    )

    col_parse, col_reset = st.columns([1, 1])
    parse_clicked = col_parse.button("Parse CV", type="primary", use_container_width=True)
    reset_clicked = col_reset.button("Reset View", use_container_width=True)

if reset_clicked:
    st.session_state.parsed_resume = None
    st.session_state.extracted_text = ""
    st.session_state.parsed_file_name = ""
    st.session_state.job_title_input = ""
    st.session_state.jobs_df = None
    st.session_state.job_error = ""
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
            with st.spinner("Parsing CV..."):
                pdf_bytes = uploaded_file.read()
                extracted_text = extract_text_from_pdf_bytes(pdf_bytes)
                parsed_resume = extract_resume_data(extracted_text, file_name=uploaded_file.name)
                st.session_state.parsed_resume = parsed_resume
                st.session_state.extracted_text = extracted_text
                st.session_state.parsed_file_name = uploaded_file.name

                skills_value = parsed_resume.get("skills")
                if isinstance(skills_value, list) and skills_value:
                    st.session_state.job_title_input = skills_value[0]
                elif isinstance(skills_value, str) and skills_value.strip():
                    st.session_state.job_title_input = skills_value.split(";")[0].strip().split("|")[0].strip()
                else:
                    st.session_state.job_title_input = ""

                st.session_state.jobs_df = None
                st.session_state.job_error = ""

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
                100
                * (sum(confidence_points[level] for level in confidence_levels) / max(len(confidence_levels), 1))
            )
            skills_count = len(st.session_state.parsed_resume.get("skills") or [])

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
                ["Overview", "Parsed Fields", "Raw Text", "Job Match"]
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

                    st.caption(
                        "Coverage bars show extracted content length per section. Higher values usually indicate richer extraction."
                    )

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
                        }
                    )

                field_df = pd.DataFrame(field_rows)
                st.dataframe(field_df, use_container_width=True, hide_index=True)

                for _, row in field_df.iterrows():
                    value_preview = row["Value"] if row["Value"] else "Not detected"
                    badge = _confidence_badge(str(row["Confidence"]))
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
                st.markdown('<div class="section-title">Find Matching Job</div>', unsafe_allow_html=True)
                st.markdown(
                    '<div class="helper-note">Suggested title comes from resume skills. You can edit it before searching.</div>',
                    unsafe_allow_html=True,
                )

                form_left, form_right = st.columns(2)
                with form_left:
                    job_title = st.text_input("Job title", key="job_title_input")
                    country_code = (
                        st.text_input("Country code", value="us", max_chars=2).lower().strip() or "us"
                    )
                with form_right:
                    serpapi_key = st.text_input(
                        "SerpApi API key",
                        value=os.environ.get("SERPAPI_API_KEY", ""),
                        type="password",
                        help="Used to run SimpleJobHunter search from this app.",
                    ).strip()

                find_clicked = st.button("Find Matching Job", type="primary", use_container_width=True)

                if find_clicked:
                    if not JOB_HUNTER_AVAILABLE:
                        st.session_state.job_error = (
                            "Job search dependencies are missing. Install: pip install google-search-results ipython"
                        )
                        st.session_state.jobs_df = None
                    elif not job_title:
                        st.session_state.job_error = "Please enter a job title before searching."
                        st.session_state.jobs_df = None
                    elif not serpapi_key:
                        st.session_state.job_error = "Please provide your SerpApi API key."
                        st.session_state.jobs_df = None
                    else:
                        with st.spinner("Searching matching jobs..."):
                            jobs_df, raw_results = search_google_jobs(
                                job_title=job_title,
                                limit=10,
                                country=country_code,
                                language="en",
                                api_key=serpapi_key,
                            )

                        if jobs_df.empty:
                            if isinstance(raw_results, dict) and raw_results.get("error"):
                                st.session_state.job_error = f"SerpApi error: {raw_results.get('error')}"
                            else:
                                st.session_state.job_error = "No jobs found for that title/location."
                            st.session_state.jobs_df = None
                        else:
                            st.session_state.job_error = ""
                            st.session_state.jobs_df = jobs_df

                if st.session_state.job_error:
                    st.error(st.session_state.job_error)
                elif st.session_state.jobs_df is not None:
                    st.markdown(
                        (
                            f'<div class="status-card">Found {len(st.session_state.jobs_df)} '
                            "matching jobs.</div>"
                        ),
                        unsafe_allow_html=True,
                    )
                    st.dataframe(st.session_state.jobs_df, use_container_width=True)

                    jobs_csv = io.StringIO()
                    st.session_state.jobs_df.to_csv(jobs_csv, index=False)
                    csv_filename = f"{st.session_state.job_title_input.lower().replace(' ', '_')}_jobs.csv"
                    st.download_button(
                        "Download Matching Jobs CSV",
                        data=jobs_csv.getvalue(),
                        file_name=csv_filename,
                        mime="text/csv",
                    )
