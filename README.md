\# PDF + CSV Reader & Automated Job Market Scout

This repository contains a Python-based CV parsing and job matching project.

The project started as a PDF + CSV reader and job hunter, and it has now been extended into a Streamlit dashboard called **Automated Job Market Scout**.

The application can parse a CV, extract structured resume fields, let users manage their parsed CVs, and search for jobs that best match the user's skillset.

Main workflow:

> Upload CV → Parse resume data → Suggest job title → Search jobs → Rank best matches

---

## Main Scripts

This project contains three main Python files:

- `app.py` — Streamlit dashboard for user/admin login, CV upload, resume parsing, job matching, ranking, and visualization.
- `read_pdf_csv.py` — reads CSV files, extracts PDF text, and includes the built-in resume parser using `pdfplumber`.
- `SimpleJobHunter.py` — searches Google Jobs through SerpApi and returns job results that can be ranked inside the dashboard.

---

## Requirements

Recommended Python version:

```text
Python 3.8+
```

Install runtime dependencies:

```powershell
python -m pip install streamlit pandas pdfplumber google-search-results ipython
```

If you are using a virtual environment, activate it first.

Example on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

## Project Structure

| File | Purpose |
|---|---|
| `app.py` | Main Streamlit dashboard. Handles user/admin flow, CV upload, parsing, job matching, ranking, and UI. |
| `read_pdf_csv.py` | Handles CSV reading, PDF text extraction, two-column CV extraction, and resume parsing. |
| `SimpleJobHunter.py` | Searches Google Jobs using SerpApi. |
| `config.py` | Stores basic app configuration such as upload types, page title, and output filename. |
| `sample_data.csv` | Sample CSV file used for testing. |
| `README.md` | Project documentation. |

Runtime/generated files such as `.venv`, `__pycache__`, `app.log`, and `dashboard_store.json` should not be committed.

Recommended `.gitignore` entries:

```gitignore
.venv/
__pycache__/
*.pyc
app.log
dashboard_store.json
*.backup
```

---

## What Changed / New Integration

The project has been improved from a simple command-line PDF/job search tool into a full dashboard application.

### Main new updates

- Added a Streamlit dashboard named **Automated Job Market Scout**.
- Added user registration and login.
- Added admin login.
- Admin can store the SerpApi key once.
- Users do not need to enter or see the SerpApi key.
- Users can upload and parse PDF CVs.
- Parsed CV information is stored locally for the logged-in user.
- Users can choose between previously parsed CVs.
- Reset View clears the current user's saved CV data.
- Job results are ranked by skill matching.
- Ranking is shown as the first column in the job table.
- The highest ranking job is shown separately as the **Best Matching Job** card.
- UI was redesigned with dashboard layout, KPI cards, tabs, confidence indicators, and better contrast.

---

## Latest Updates

This project was improved in four main areas:

1. Resume parser quality
2. Job matching integration
3. Streamlit dashboard design
4. User/admin control

---

## 1. Resume Parser Improvements (`read_pdf_csv.py`)

### Better PDF extraction

The parser uses `pdfplumber` to extract text from PDF files and supports more advanced CV layouts.

### Better two-column extraction

Many modern CVs use two-column layouts. Normal PDF extraction can mix the left and right columns together.

To improve this, the parser now:

- detects large horizontal gaps between words,
- checks gaps inside the same row,
- separates left and right column text,
- rebuilds extracted text in a better reading order,
- uses fallback logic if the layout is not clearly two-column.

This helps with modern CV templates.

### Better name extraction

The parser was improved so it does not accidentally select skill phrases or language-level phrases as the candidate name.

For example, phrases like these should not become the full name:

- `Time management`
- `Full Professional Proficiency`
- `Communication`

### Better section extraction

The parser includes improved logic for common CV sections such as:

- education
- experience
- skills
- contact details

It also handles different heading styles more reliably.

---

## 2. Streamlit Dashboard (`app.py`)

The project now includes a full Python UI built with Streamlit.

### Current UI capabilities

- Upload and parse a single PDF CV
- View extracted raw text
- View parsed structured fields
- View confidence estimate
- View section coverage chart
- Download parsed data as CSV
- Search matching jobs via SerpApi
- Rank job results by skill match
- Display best matching job separately
- Download matching jobs as CSV
- Register/login as user
- Login as admin
- Store SerpApi key in admin view
- View and remove users from admin view
- Select previously parsed CVs
- Reset saved CV data

---

## 3. User Dashboard

The user mode allows a normal user to work with their own CV data.

### User can:

- register with username and password,
- login,
- upload a PDF CV,
- parse the CV,
- view parsed fields,
- view raw PDF text,
- search matching jobs,
- select previously parsed CVs,
- reset saved CV data,
- download parsed CSV,
- download matching jobs CSV.

After login, the user gets access to the dashboard.

If the user is not logged in, the app shows:

```text
Login with a username from the sidebar to continue.
```

---

## 4. Admin Dashboard

The admin mode is used to manage the application.

### Admin can:

- login as admin,
- store the SerpApi key,
- view registered users,
- remove users.

The SerpApi key is only entered in the admin view.  
Normal users do not need to provide the key.

Default admin password:

```text
admin123
```

You can also set another admin password before running the app:

```powershell
$env:APP_ADMIN_PASSWORD = "your-password"
```

If no environment variable is set, the app uses the default password:

```text
admin123
```

---

## 5. Job Matching and Ranking

The job search is handled through `SimpleJobHunter.py` and used inside `app.py`.

### How job matching works

1. User uploads and parses a CV.
2. The app suggests a job title from the user's experience or skills.
3. User can edit the suggested job title.
4. User enters a country code.
5. App searches Google Jobs through SerpApi.
6. Results are ranked by comparing CV skills with job descriptions.
7. Highest ranking jobs appear first.
8. Best result is displayed separately.

### Job table includes:

- `Ranking`
- `Ranking Confidence`
- `Matched Skills`
- job title
- company
- location
- description
- apply link if available

The **Ranking** column is the first column because the best jobs should be shown first.

---

## 6. Best Matching Job Card

After job search, the highest-ranked job is displayed separately in a card.

This card shows:

- job title,
- company,
- ranking score,
- matched skills.

This makes the best result easier to see during a thesis demo.

---

## 7. Confidence Indicators

The dashboard includes confidence indicators for extracted fields.

Each parsed field has a confidence level:

- High
- Medium
- Low

This helps explain how reliable each extracted value is.

The app also shows an overall parse confidence estimate.

---

## 8. CV History / CV Selector

When a user parses CVs, the app stores them locally for that user.

The user can choose a previously parsed CV from a selector and load it again.

This is useful when the user has uploaded more than one CV.

The **Reset View** button clears the current user's saved CV data and history.

---

## 9. Local Data Storage

The app stores local dashboard data in:

```text
dashboard_store.json
```

This file is created automatically when:

- a user registers,
- a CV is parsed,
- job results are saved,
- admin stores the SerpApi key.

It may contain:

- usernames,
- password hashes,
- parsed CV data,
- saved job results,
- SerpApi key.

Because of this, `dashboard_store.json` should not be pushed to GitHub or GitLab.

---

## Run from Streamlit UI

Go to the project folder:

```powershell
cd C:\Users\Raul\Desktop\thesis\thesis
```

Run the app:

```powershell
C:\Users\Raul\Desktop\thesis\.venv\Scripts\python.exe -m streamlit run app.py
```

If Streamlit is available globally, you can also run:

```powershell
streamlit run app.py
```

Then open the local URL shown in the terminal, usually:

```text
http://localhost:8501
```

---

## How to Use the Streamlit App

### 1. Admin setup

1. Open the app.
2. Select **Admin** from the sidebar.
3. Login using the admin password.
4. Paste your SerpApi key.
5. Click **Save API key**.
6. Logout from admin mode.

### 2. User registration

1. Select **User** from the sidebar.
2. Choose **Register**.
3. Enter username.
4. Enter password and confirm it.
5. Click **Register**.

### 3. User login

1. Choose **Login**.
2. Enter username and password.
3. Click **Login**.

### 4. Parse CV

1. Upload a PDF CV.
2. Click **Parse CV**.
3. Check the extracted fields.
4. Review raw extracted text if needed.
5. Download parsed CSV if needed.

### 5. Search matching jobs

1. Open the **Job Match** tab.
2. Check or edit the suggested job title.
3. Enter country code, for example:
   - `us`
   - `hu`
   - `tr`
4. Click **Find Matching Job**.
5. Review the best matching job card.
6. Review the ranked job table.
7. Download matching jobs CSV if needed.

---

## Command Line Usage

The project can still be used from the command line.

### Default sample run

```powershell
python .\read_pdf_csv.py
```

### Custom files

```powershell
python .\read_pdf_csv.py .\your_file.pdf .\your_file.csv
```

### Integrated resume parsing from main script

This runs the standard CSV/PDF reader and also executes built-in CV parsing from inside `read_pdf_csv.py`.

```powershell
python .\read_pdf_csv.py ".\Raul's Resume.pdf" .\sample_data.csv --parse-resume --resume-output .\parsed_resumes_from_main.csv
```

### Parse and write JSON

```powershell
python .\read_pdf_csv.py ".\Raul's Resume.pdf" .\sample_data.csv --parse-resume --resume-output .\parsed_resumes.json
```

---

## Job Search Script (`SimpleJobHunter.py`)

`SimpleJobHunter.py` searches Google Jobs using SerpApi and exports results to CSV.

It can be used separately from the Streamlit UI.

### Run JobHunter

```powershell
python .\SimpleJobHunter.py
```

The script asks for:

- SerpApi API key,
- job title,
- country code.

It then saves output as:

```text
<job_title>_jobs.csv
```

---

## SerpApi Key Options

Inside the Streamlit app, the SerpApi key is stored from the admin dashboard.

For command-line usage, the script may prompt for the key. You can also set it in your session.

PowerShell temporary session:

```powershell
$env:SERPAPI_API_KEY = "YOUR_KEY"
```

Permanent user environment variable:

```powershell
[Environment]::SetEnvironmentVariable("SERPAPI_API_KEY","YOUR_KEY","User")
```

---

## Error Handling Included

The project includes handling for common issues such as:

- missing files,
- invalid file format,
- invalid PDF files,
- CSV format issues,
- empty extracted text,
- missing SerpApi key,
- no job results returned,
- unavailable job search dependencies.

---

## Sample Test Files

The project includes sample files such as:

- `sample_data.csv`
- sample PDF files if available in the folder

These can be used for testing the parser and command-line behavior.

---

## Project Summary

Automated Job Market Scout combines CV parsing, dashboard visualization, user/admin management, and ranked job matching in one workflow.

The project demonstrates how a CV can be transformed into structured data and used to support job search decisions through ranked recommendations.