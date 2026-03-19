import argparse
import csv
import importlib
import json
import re
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

EXPECTED_COLUMNS = ["name", "surname", "email", "number", "skills", "location"]


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    try:
        pdfplumber = importlib.import_module("pdfplumber")
    except ImportError as exc:
        raise SystemExit(
            "pdfplumber is required to run this script. Install it with: pip install pdfplumber"
        ) from exc

    text_parts: List[str] = []
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text(x_tolerance=2, y_tolerance=2)
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def _clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n\n", text)
    return text.strip()


def _extract_email(text: str) -> Optional[str]:
    match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    return match.group(0) if match else None


def _extract_phone(text: str) -> Optional[str]:
    pattern = re.compile(r"\+?\d[\d\-\s\(\)]{6,}\d")
    for line in text.splitlines():
        match = pattern.search(line)
        if not match:
            continue
        phone = match.group(0).strip()
        digits = re.sub(r"\D", "", phone)
        if 9 <= len(digits) <= 15:
            return phone
    return None


def _extract_linkedin(text: str) -> Optional[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for index, line in enumerate(lines):
        match = re.search(
            r"(https?://)?(www\.)?linkedin\.com/in/[A-Za-z0-9\-_/%]+",
            line,
            re.IGNORECASE,
        )
        if not match:
            continue

        url = match.group(0).rstrip(".,;)")
        if url.endswith("-") and index + 1 < len(lines):
            next_line = lines[index + 1]
            next_match = re.match(r"^[A-Za-z0-9\-_]{2,60}$", next_line)
            if next_match:
                url = f"{url}{next_match.group(0)}"
        return url
    return None


def _extract_name_and_surname(text: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    ignore_words = {
        "resume",
        "cv",
        "curriculum",
        "vitae",
        "email",
        "phone",
        "linkedin",
        "github",
        "address",
        "profile",
        "summary",
        "experience",
        "education",
        "skills",
    }

    for line in lines[:10]:
        low = line.lower()
        if "@" in line:
            continue
        if re.search(r"\+?\d[\d\-\s\(\)]{7,}\d", line):
            continue
        if "linkedin.com" in low or "github.com" in low or "http" in low:
            continue
        if any(word in low for word in ignore_words):
            continue

        words = line.split()
        if 2 <= len(words) <= 4 and all(word.replace("-", "").isalpha() for word in words):
            return line, words[0], words[-1]

    return None, None, None


def _extract_address(text: str) -> Optional[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines[:30]:
        if re.match(r"^[A-Za-z .'-]{2,},\s*[A-Za-z .'-]{2,}$", line) and len(line) <= 60:
            return line
    return None


def _extract_section(text: str, section_names: List[str]) -> Optional[str]:
    lines = text.splitlines()
    section_text: List[str] = []
    capture = False

    all_headings = {
        "summary",
        "profile",
        "experience",
        "work experience",
        "employment",
        "education",
        "skills",
        "projects",
        "certifications",
        "languages",
        "awards",
        "interests",
        "publications",
        "volunteer",
        "contact",
    }

    normalized_targets = {name.lower().strip() for name in section_names}
    for raw_line in lines:
        line = raw_line.strip()
        lowered = line.lower()
        if lowered in normalized_targets:
            capture = True
            continue
        if capture and lowered in all_headings:
            break
        if capture and line:
            section_text.append(line)

    result = "\n".join(section_text)
    return result if result else None


def _extract_skills(text: str) -> Optional[List[str]]:
    section = _extract_section(text, ["skills", "technical skills", "core skills"])
    if not section:
        return None
    raw_items = re.split(r"[,•\n|]+", section)
    items = [item.strip() for item in raw_items if item.strip()]
    return items[:30] if items else None


def extract_resume_data(text: str, file_name: Optional[str] = None) -> Dict[str, Any]:
    cleaned = _clean_text(text)
    full_name, first_name, surname = _extract_name_and_surname(cleaned)

    return {
        "file_name": file_name,
        "full_name": full_name,
        "name": first_name,
        "surname": surname,
        "email": _extract_email(cleaned),
        "phone": _extract_phone(cleaned),
        "address": _extract_address(cleaned),
        "linkedin": _extract_linkedin(cleaned),
        "skills": _extract_skills(cleaned),
        "education": _extract_section(cleaned, ["education", "academic background", "academic qualifications"]),
        "experience": _extract_section(cleaned, ["experience", "work experience", "employment history", "professional experience"]),
    }


def _largest_column_gap(words: List[Dict[str, Any]], page_width: float) -> float | None:
    x_positions = sorted(word["x0"] for word in words if "x0" in word)
    if len(x_positions) < 20:
        return None

    max_gap = 0.0
    gap_index = -1
    for index in range(len(x_positions) - 1):
        gap = x_positions[index + 1] - x_positions[index]
        if gap > max_gap:
            max_gap = gap
            gap_index = index

    # Require a meaningful gap before splitting into columns.
    min_gap = max(50.0, page_width * 0.12)
    if gap_index == -1 or max_gap < min_gap:
        return None

    return (x_positions[gap_index] + x_positions[gap_index + 1]) / 2.0


def _lines_from_words(words: List[Dict[str, Any]], y_tolerance: float = 3.0) -> List[str]:
    if not words:
        return []

    sorted_words = sorted(words, key=lambda word: (word.get("top", 0.0), word.get("x0", 0.0)))
    lines: List[List[Dict[str, Any]]] = []

    for word in sorted_words:
        if not lines:
            lines.append([word])
            continue

        previous_top = lines[-1][0].get("top", 0.0)
        current_top = word.get("top", 0.0)
        if abs(current_top - previous_top) <= y_tolerance:
            lines[-1].append(word)
        else:
            lines.append([word])

    rendered_lines: List[str] = []
    for line_words in lines:
        ordered_words = sorted(line_words, key=lambda word: word.get("x0", 0.0))
        text = " ".join(word.get("text", "").strip() for word in ordered_words).strip()
        if text:
            rendered_lines.append(text)

    return rendered_lines


def _extract_page_text_smart(page: Any) -> str:
    words = page.extract_words(x_tolerance=2, y_tolerance=2, use_text_flow=True)
    if not words:
        return page.extract_text() or ""

    split_x = _largest_column_gap(words, float(page.width))
    if split_x is None:
        return "\n".join(_lines_from_words(words))

    left_words = [word for word in words if float(word.get("x0", 0.0)) <= split_x]
    right_words = [word for word in words if float(word.get("x0", 0.0)) > split_x]

    left_text = "\n".join(_lines_from_words(left_words))
    right_text = "\n".join(_lines_from_words(right_words))

    sections = [section for section in [left_text, right_text] if section]
    return "\n\n".join(sections)


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
        pdfplumber = importlib.import_module("pdfplumber")
    except ImportError as exc:
        raise SystemExit(
            "pdfplumber is required to run this script. Install it with: pip install pdfplumber"
        ) from exc

    try:
        with pdfplumber.open(pdf_path) as pdf:
            extracted_text_parts: List[str] = []
            for index, page in enumerate(pdf.pages, start=1):
                page_text = _extract_page_text_smart(page)
                extracted_text_parts.append(f"--- Page {index} ---\n{page_text}")
    except Exception as exc:
        raise ValueError(f"Unable to read PDF file: {pdf_path}") from exc

    return "\n\n".join(extracted_text_parts).strip()


def discover_file(
    file_extension: str,
    search_dir: Path,
    preferred_name: str | None = None,
) -> Path:
    working_dir = search_dir
    if preferred_name:
        preferred_path = working_dir / preferred_name
        if preferred_path.exists() and preferred_path.suffix.lower() == file_extension:
            return preferred_path

    matches = sorted(
        path for path in working_dir.glob(f"*{file_extension}") if path.is_file()
    )
    if not matches:
        raise FileNotFoundError(
            f"No {file_extension} files found in: {working_dir}. "
            "Provide an explicit file path as an argument."
        )

    return matches[0]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read and print structured CSV data and extract text from a PDF file."
    )
    parser.add_argument(
        "pdf_path",
        nargs="?",
        default=None,
        help=(
            "Path to the PDF file. If omitted, the script auto-discovers a PDF file "
            "in the current working directory."
        ),
    )
    parser.add_argument(
        "csv_path",
        nargs="?",
        default=None,
        help=(
            "Path to the CSV file. If omitted, the script auto-discovers a CSV file "
            "in the current working directory."
        ),
    )
    parser.add_argument(
        "--parse-resume",
        action="store_true",
        help="Run built-in CVPlumber resume parsing and export parsed fields to CSV.",
    )
    parser.add_argument(
        "--resume-output",
        default="parsed_resumes.csv",
        help="Output path for resume parser data (.csv or .json) when --parse-resume is used.",
    )
    return parser.parse_args()


def _single_line(value: str) -> str:
    compact = re.sub(r"\s*\n\s*", " | ", value.strip())
    compact = re.sub(r"[ \t]+", " ", compact)
    return compact.strip(" |")


def _prettify_resume_record(parsed: Dict[str, Any]) -> Dict[str, str]:
    pretty: Dict[str, str] = {}
    for key, value in parsed.items():
        if value is None:
            pretty[key] = ""
        elif isinstance(value, list):
            pretty[key] = "; ".join(_single_line(str(item)) for item in value if str(item).strip())
        elif isinstance(value, str):
            pretty[key] = _single_line(value)
        else:
            pretty[key] = str(value)
    return pretty


def parse_resume_with_cvplumber(pdf_path: Path, output_path: Path) -> Dict[str, Any]:
    file_bytes = pdf_path.read_bytes()
    pdf_text = extract_text_from_pdf_bytes(file_bytes)
    parsed = extract_resume_data(pdf_text, file_name=pdf_path.name)
    pretty_parsed = _prettify_resume_record(parsed)

    if output_path.suffix.lower() == ".json":
        output_path.write_text(
            json.dumps(pretty_parsed, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    else:
        df = pd.DataFrame([pretty_parsed])
        df.to_csv(output_path, index=False)

    return pretty_parsed


def main() -> None:
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    pdf_path = Path(args.pdf_path) if args.pdf_path else discover_file(".pdf", script_dir)
    csv_path = Path(args.csv_path) if args.csv_path else discover_file(".csv", script_dir)

    try:
        csv_rows = read_csv_file(csv_path)
        print("=== Parsed CSV Data ===")
        print_csv_rows(csv_rows)

        if args.parse_resume:
            output_path = Path(args.resume_output).expanduser().resolve()
            parsed_resume = parse_resume_with_cvplumber(pdf_path, output_path)

            print("\n=== Parsed Resume Fields (CVPlumber) ===")
            for key, value in parsed_resume.items():
                print(f"{key}: {value}")
            print(f"Saved resume parser CSV to: {output_path}")
        else:
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