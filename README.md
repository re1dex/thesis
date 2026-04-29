# 📄 PDF + CSV Reader & Automated Job Market Scout

---

## 🚀 Overview

This repository contains a web-based job discovery system for job seekers.

The project started as a PDF + CSV reader and job hunter, and it has now been extended into a Streamlit dashboard called **Automated Job Market Scout**.

The application can parse a CV, extract structured resume fields, let users inspect which parts of the CV are machine readable, and support job discovery through SerpApi-based search.

---

### 🔄 Main Workflow

> **Upload CV → Extract text → Parse fields → Inspect machine-readability → Visualize results → Export data → Search jobs**

---

## 🎓 Thesis Framing

### 👤 Target user

* Job seeker

### 🧩 Project type

* Web-based job discovery system

### 📌 Claim level

* Supports job discovery

---

### ❗ Problem statement

The project is not only about parsing a CV and finding jobs.
It also helps the user understand which fields or parts of the CV are machine readable and which parts may need improvement.

---

### 🧠 Thesis argument

This project addresses two common pain points:

1. A CV can look good to a human but still be poorly machine readable.
2. A job seeker can search for a desired title without knowing how their actual skills match available roles.

**Solution:**
➡️ The **Automated Job Market Scout** supports CV inspection and job discovery in one workflow.

---

### 🎯 Objectives

* Upload
* Extract
* Parse
* Inspect
* Visualize
* Export
* Search job

---

### 🚫 Out of scope

* Full ATS system
* CV rewriting
* Best-job recommendation engine

---

### ⭐ Main value

* Users can see whether important CV fields are machine readable.

---

## 📂 Main Scripts

| File                 | Purpose                                                                          |
| -------------------- | -------------------------------------------------------------------------------- |
| `app.py`             | Streamlit dashboard for login, CV parsing, job discovery, ranking, visualization |
| `read_pdf_csv.py`    | PDF + CSV processing and resume parsing                                          |
| `SimpleJobHunter.py` | Job discovery via SerpApi                                                        |

---

## ⚙️ Requirements

**Python version:**

```text
Python 3.8+
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

---

## 🗂️ Project Structure

| File                   | Purpose          |
| ---------------------- | ---------------- |
| `app.py`               | Main dashboard   |
| `read_pdf_csv.py`      | Parsing logic    |
| `SimpleJobHunter.py`   | Job discovery    |
| `config.py`            | App config       |
| `sample_resumes/`      | Test CVs         |
| `example_outputs/`     | Output examples  |
| `parser_evaluation.md` | Evaluation notes |
| `README.md`            | Documentation    |

---

## 🔄 What Changed / New Integration

The project evolved from a simple script into a full dashboard.

### ✨ Key Improvements

* Streamlit dashboard (**Automated Job Market Scout**)
* User authentication
* Admin API key storage
* CV upload + parsing
* CV history tracking
* Job ranking system
* Best job highlight card
* Improved UI (KPI cards, tabs, indicators)

---

## 🧠 Resume Parser Improvements (`read_pdf_csv.py`)

### 📄 Better PDF extraction

* Uses `pdfplumber`
* Handles modern CV layouts

### 🧩 Two-column handling

* Detects layout gaps
* Separates columns
* Reconstructs reading order

### 👤 Name extraction

Avoids false names like:

* `Time management`
* `Communication`
* `Full Professional Proficiency`

### 📑 Section extraction

Handles:

* education
* experience
* skills
* contact info

---

## 🖥️ Streamlit Dashboard (`app.py`)

### Features

* CV upload + parsing
* Raw text view
* Structured data view
* Confidence scoring
* Charts & visualization
* Job discovery
* Ranking
* CSV export
* User/admin roles

---

## 👤 User Dashboard

Users can:

* register & login
* upload CV
* parse CV
* inspect results
* search jobs
* manage history
* export CSV

---

## 🔐 Admin Dashboard

Admin can:

* login
* store SerpApi key

---

## 🧑‍💼 Recruiter Panel

Recruiter can:

* search job titles
* view matched users
* see contact info

---

## 🔎 Job Discovery

### Workflow

1. Parse CV
2. Suggest job title
3. Search jobs
4. Rank results
5. Show best job

---

### 📊 Job Table

* Ranking
* Ranking Confidence
* Matched Skills
* Job details

---

## 🏆 Best Job Card

Displays:

* title
* company
* ranking
* matched skills

---

## 📊 Confidence Indicators

Each field is labeled:

* High
* Medium
* Low

Also includes overall confidence score.

---

## 📁 CV History

* Stores previous CVs
* Allows reloading
* Reset option available

---

## 💾 Local Storage

```text
dashboard_store.json
```

Contains:

* users
* CV data
* job results
* API key

⚠️ Do not push to Git.

---

## ▶️ Run the App

```powershell
streamlit run app.py
```

Open:

```text
http://localhost:8501
```

---

## 🧪 Tests

Run:

```powershell
pytest
```

Covers:

* parser logic
* extraction accuracy
* edge cases

---

## 📊 Parser Evaluation

```text
evaluation/parser_evaluation.csv
```

Shows:

* extracted fields
* correctness

---

## 📦 Example Outputs

```text
example_outputs/
```

Includes:

* parsed CV
* job results

---

## ⚠️ Error Handling

Handles:

* invalid files
* missing API key
* parsing issues
* empty results

---

## 🏁 Project Summary

Automated Job Market Scout combines CV parsing, visualization, and job discovery.

It helps users understand machine-readability of their CV and supports better job search decisions.
