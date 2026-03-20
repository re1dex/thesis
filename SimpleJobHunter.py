# Install once in terminal: pip install google-search-results pandas ipython

import pandas as pd
from serpapi import GoogleSearch
from getpass import getpass
from IPython.display import display
from pathlib import Path

# Try to import resume parser helpers; if unavailable, continue without parser.
try:
    from read_pdf_csv import extract_text_from_pdf_bytes, extract_resume_data, discover_file
    RESUME_PARSER_AVAILABLE = True
except Exception:
    extract_text_from_pdf_bytes = None
    extract_resume_data = None
    discover_file = None
    RESUME_PARSER_AVAILABLE = False

SERPAPI_API_KEY = getpass("Enter your SerpApi API key: ")


def extract_apply_links(job):
    links = []
    for option in job.get("apply_options", []):
        if isinstance(option, dict):
            title = option.get("title", "")
            link = option.get("link", "")
            if title or link:
                links.append({
                    "source": title,
                    "url": link
                })
    return links


def search_google_jobs(job_title, limit=10, country="us", language="en"):
    params = {
        "engine": "google_jobs",
        "q": job_title,
        "hl": language,
        "gl": country,
        "api_key": SERPAPI_API_KEY
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    jobs = results.get("jobs_results", [])
    rows = []

    for job in jobs[:limit]:
        apply_links = extract_apply_links(job)

        rows.append({
            "job_title": job.get("title"),
            "company": job.get("company_name"),
            "location": job.get("location"),
            "posted_by": job.get("via"),
            "schedule_type": (
                job.get("detected_extensions", {}).get("schedule_type")
                if isinstance(job.get("detected_extensions"), dict) else None
            ),
            "posted_at": (
                job.get("detected_extensions", {}).get("posted_at")
                if isinstance(job.get("detected_extensions"), dict) else None
            ),
            "description": job.get("description"),
            "apply_sources": ", ".join(
                [x["source"] for x in apply_links if x.get("source")]
            ),
            "apply_urls": " | ".join(
                [x["url"] for x in apply_links if x.get("url")]
            )
        })

    return pd.DataFrame(rows), results


def suggest_job_title_from_resume(resume_path):
    if resume_path.exists() and resume_path.suffix.lower() == ".pdf" and RESUME_PARSER_AVAILABLE:
        try:
            pdf_bytes = resume_path.read_bytes()
            text = extract_text_from_pdf_bytes(pdf_bytes)
            parsed = extract_resume_data(text, file_name=resume_path.name)
            skills = parsed.get("skills") or []
            if isinstance(skills, list) and skills:
                return skills[0]
            elif isinstance(skills, str) and skills:
                # if skills came as a single string, try splitting
                return skills.split(";")[0].strip().split("|")[0]
        except Exception as exc:
            print(f"Resume parse failed: {exc}")
    else:
        if not RESUME_PARSER_AVAILABLE:
            print("Resume parser not available (read_pdf_csv.py import failed).")
        else:
            print("Resume file not found or invalid; skipping.")
    return None


# Ask for an optional resume to auto-suggest a job title based on skills
# Attempt to auto-discover a PDF in the script folder when the parser is available.
script_dir = Path(__file__).resolve().parent
suggested_title = None
if RESUME_PARSER_AVAILABLE:
    try:
        pdf_path = discover_file(".pdf", script_dir)
        print(f"Found PDF: {pdf_path.name} — attempting to parse for suggested job title.")
        suggested_title = suggest_job_title_from_resume(pdf_path)
    except FileNotFoundError:
        # No PDF discovered; fall back to asking the user
        resume_path_input = input("Path to resume PDF to auto-suggest job title (leave blank to skip): ").strip()
        suggested_title = suggest_job_title_from_resume(Path(resume_path_input)) if resume_path_input else None
else:
    resume_path_input = input("Path to resume PDF to auto-suggest job title (leave blank to skip): ").strip()
    suggested_title = suggest_job_title_from_resume(Path(resume_path_input)) if resume_path_input else None

if suggested_title:
    job_title = input(f"Enter job title (suggested: {suggested_title}) [Enter to use suggestion]: ").strip() or suggested_title
else:
    job_title = input("Enter job title: ").strip()

country = input("Enter country code (default: us): ").strip().lower() or "us"
jobs_df, raw_results = search_google_jobs(job_title, limit=10, country=country, language="en")

if jobs_df.empty:
    if isinstance(raw_results, dict) and raw_results.get("error"):
        print(f"SerpApi error: {raw_results.get('error')}")
    else:
        print("No jobs found.")
        if isinstance(raw_results, dict):
            print(
                "Debug info: "
                f"jobs_results={len(raw_results.get('jobs_results', []))}, "
                f"search_metadata_status={raw_results.get('search_metadata', {}).get('status')}"
            )
else:
    display(jobs_df)
    output_file = f"{job_title.lower().replace(' ', '_')}_jobs.csv"
    jobs_df.to_csv(output_file, index=False)
    print(f"Saved: {output_file}")
