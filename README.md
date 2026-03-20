# PDF + CSV Reader & Job Hunter

This repository contains two main scripts that work together to parse resumes and search jobs:

- `read_pdf_csv.py` — reads a structured CSV, extracts text from a PDF, and includes a built-in resume parser using `pdfplumber`.
- `SimpleJobHunter.py` — searches Google Jobs (via SerpApi) and can optionally use the resume parser to auto-suggest a job title.

## Requirements

- Python 3.8+
- Install runtime dependencies:
  - For resume parsing / CSV/JSON export:
    ```
    python -m pip install pdfplumber pandas
    ```
  - For job search:
    ```
    python -m pip install google-search-results pandas ipython
    ```

## What changed / new integration

- `SimpleJobHunter.py` now optionally imports the parser helpers from `read_pdf_csv.py`:
  - `extract_text_from_pdf_bytes`, `extract_resume_data`, and `discover_file` are used when available.
- Auto-discovery of a PDF:
  - When the parser is available, `SimpleJobHunter.py` will auto-discover the first `.pdf` in the script folder and attempt to parse it.
  - If no PDF is found, the script falls back to prompting you for a path.
- Job-title suggestion from resume:
  - The parser extracts `skills` from the resume and the first skill is suggested as a job title. You can accept the suggestion by pressing Enter or type a different title.
- `read_pdf_csv.py` supports writing parsed resume output as CSV (default) or JSON via `--resume-output`.

## Code structure

- `read_csv_file(csv_path)`
	- Validates CSV path and extension
	- Validates header columns
	- Returns parsed row data
- `read_pdf_file(pdf_path)`
	- Validates PDF path and extension
	- Extracts text from each page
- `main()`
	- Calls both CSV and PDF functions
	- Prints output to console
	- Handles common errors

## Error handling included

- Missing files (`FileNotFoundError`)
- Invalid file format (`.csv` / `.pdf` checks)
- CSV format issues (empty/missing header, wrong columns)
- PDF read failures

## Sample test files added

- `sample_data.csv`
- `sample_document.pdf`

The PDF sample contains the same people data as the CSV sample.

## Run from command line

### Default sample run (short command)

```powershell
python .\read_pdf_csv.py
```

### Custom files

```powershell
python .\read_pdf_csv.py .\your_file.pdf .\your_file.csv
```

### Integrated resume parsing from main script

This runs the standard CSV+PDF reader and also executes built-in CVPlumber parsing from inside `read_pdf_csv.py`.

```powershell
python .\read_pdf_csv.py ".\Raul's Resume.pdf" .\sample_data.csv --parse-resume --resume-output .\parsed_resumes_from_main.csv
```

### If pdfplumber is missing

```powershell
python -m pip install pdfplumber
```

## Job Search Script (SerpApi)

`SimpleJobHunter.py` searches Google Jobs using SerpApi and exports results to CSV.

- Prompts for SerpApi API key
- Prompts for job title and country code
- Fetches Google Jobs listings
- Saves output as `<job_title>_jobs.csv`

### Run JobHunter

```powershell
python .\SimpleJobHunter.py
```

### Install dependencies for JobHunter

```powershell
python -m pip install google-search-results pandas ipython
```

## Usage

1) Parse a single resume and write CSV (default):

PowerShell

```powershell
python "C:\Users\excfnr\Desktop\thesis\read_pdf_csv.py" --parse-resume
```

- This will auto-discover a `.pdf` in the script folder (if you omit the `pdf_path` arg) and write `parsed_resumes.csv` by default.

2) Parse and write JSON:

```powershell
python "C:\Users\excfnr\Desktop\thesis\read_pdf_csv.py" --parse-resume --resume-output "parsed_resumes.json"
```

3) Run the job search and use resume auto-suggestion (interactive):

- Ensure `read_pdf_csv.py` and `SimpleJobHunter.py` are in the same folder.
- Run:

```powershell
python "C:\Users\excfnr\Desktop\thesis\SimpleJobHunter.py"
```

- Prompts you will see:
  - Enter your SerpApi API key (hidden)
  - If a resume PDF exists in the script folder the script will print the found file and attempt parsing automatically. Otherwise you will be prompted:
    Path to resume PDF to auto-suggest job title (leave blank to skip):
  - Enter or accept the suggested job title
  - Enter country code (default: `us`)

- Results are displayed and saved as `<job_title>_jobs.csv` in the script folder.

## SerpApi key options

- The script prompts for the SerpApi key at runtime. You can also set it in your session to avoid typing it:

PowerShell (temporary for session):
```powershell
$env:SERPAPI_API_KEY = "YOUR_KEY"
```

Or set it permanently:
```powershell
[Environment]::SetEnvironmentVariable("SERPAPI_API_KEY","YOUR_KEY","User")
```

## Notes and suggestions

- Keep both scripts in the same folder so `SimpleJobHunter.py` can import the parser helpers from `read_pdf_csv.py`.
- `read_pdf_csv.py` is conservative by default: resume parsing and file writes only occur when `--parse-resume` is provided. `SimpleJobHunter.py` uses the parser only to suggest job titles and does not write parsed files unless you call `read_pdf_csv.py` directly.
- If you want improvements (batch parsing, mapping skills to cleaner job titles, or saving parsed resumes from the job-hunter run), open an issue or request the change and it can be added.

## License

This repository contains sample code for personal use. No license file is included.