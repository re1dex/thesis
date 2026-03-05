import argparse
import csv
from pathlib import Path
from typing import Dict, List

try:
    from PyPDF2 import PdfReader
except ImportError as exc:
    raise SystemExit(
        "PyPDF2 is required to run this script. Install it with: pip install PyPDF2"
    ) from exc


EXPECTED_COLUMNS = ["name", "surname", "email", "number", "skills", "location"]
DEFAULT_PDF_PATH = "sample_document.pdf"
DEFAULT_CSV_PATH = "sample_data.csv"


def read_csv_file(csv_path: Path) -> List[Dict[str, str]]:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    if csv_path.suffix.lower() != ".csv":
        raise ValueError(f"Invalid CSV file format: {csv_path}. Expected a .csv file.")

    rows: List[Dict[str, str]] = []

    with csv_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None:
            raise ValueError("CSV file is empty or missing a header row.")

        actual_columns = [column.strip() for column in reader.fieldnames]
        if actual_columns != EXPECTED_COLUMNS:
            raise ValueError(
                "Invalid CSV columns. "
                f"Expected: {EXPECTED_COLUMNS}. "
                f"Found: {actual_columns}"
            )

        for row in reader:
            parsed_row = {key: (value.strip() if value is not None else "") for key, value in row.items()}
            rows.append(parsed_row)

    return rows


def print_csv_rows(rows: List[Dict[str, str]]) -> None:
    for row in rows:
        print(f"Name: {row.get('name', '')}")
        print(f"Surname: {row.get('surname', '')}")
        print(f"Email: {row.get('email', '')}")
        print(f"Number: {row.get('number', '')}")
        print(f"Skills: {row.get('skills', '')}")
        print(f"Location: {row.get('location', '')}")
        print("-------------------------")


def read_pdf_file(pdf_path: Path) -> str:
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"Invalid PDF file format: {pdf_path}. Expected a .pdf file.")

    try:
        reader = PdfReader(str(pdf_path))
    except Exception as exc:
        raise ValueError(f"Unable to read PDF file: {pdf_path}") from exc

    extracted_text_parts: List[str] = []
    for index, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        extracted_text_parts.append(f"--- Page {index} ---\n{page_text}")

    return "\n\n".join(extracted_text_parts).strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read and print structured CSV data and extract text from a PDF file."
    )
    parser.add_argument(
        "pdf_path",
        nargs="?",
        default=DEFAULT_PDF_PATH,
        help=f"Path to the PDF file (default: {DEFAULT_PDF_PATH})",
    )
    parser.add_argument(
        "csv_path",
        nargs="?",
        default=DEFAULT_CSV_PATH,
        help=f"Path to the CSV file (default: {DEFAULT_CSV_PATH})",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pdf_path = Path(args.pdf_path)
    csv_path = Path(args.csv_path)

    try:
        csv_rows = read_csv_file(csv_path)
        print("=== Parsed CSV Data ===")
        print_csv_rows(csv_rows)

        pdf_text = read_pdf_file(pdf_path)
        print("\n=== Extracted PDF Text ===")
        if pdf_text:
            print(pdf_text)
        else:
            print("No extractable text found in the PDF.")

    except (FileNotFoundError, ValueError, csv.Error) as exc:
        print(f"Error: {exc}")


if __name__ == "__main__":
    main()