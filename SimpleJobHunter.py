# Install once in terminal: pip install google-search-results pandas ipython

import pandas as pd
from serpapi import GoogleSearch
from getpass import getpass
from IPython.display import display

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
