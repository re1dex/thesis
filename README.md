# PDF + CSV Reader Script

This project implements a Python command-line script that reads data from both a CSV file and a PDF file, based on the requested requirements.

## What was implemented

- Script: `read_pdf_csv.py`
- Reads CSV file with expected columns:
	- `name,surname,email,number,skills,location`
- Parses each CSV row into structured data
- Prints CSV fields in a readable format:
	- `Name`, `Surname`, `Email`, `Number`, `Skills`, `Location`
- Opens PDF file and extracts text content
- Prints extracted PDF text to console
- Uses:
	- `csv` (built-in) for CSV parsing
	- `PyPDF2` for PDF reading

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

### If PyPDF2 is missing

```powershell
python -m pip install PyPDF2
```