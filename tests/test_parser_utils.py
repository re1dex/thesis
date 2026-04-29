from read_pdf_csv import _extract_email, _extract_phone, extract_resume_data


def test_extract_email_handles_normal_address():
    assert _extract_email("Contact: test.user@example.com") == "test.user@example.com"


def test_extract_email_returns_none_when_missing():
    assert _extract_email("No email address here") is None


def test_extract_phone_handles_international_number():
    phone = _extract_phone("Phone: +36 30 123 4567")
    assert phone is not None
    assert "36" in phone


def test_extract_phone_returns_none_when_missing():
    assert _extract_phone("No phone number here") is None


def test_extract_resume_data_returns_expected_keys():
    parsed = extract_resume_data(
        """
        Raul Zeynalov
        Budapest, Hungary
        raul@example.com
        +36 30 123 4567

        Skills
        Python, SQL, Data Analysis

        Experience
        Python Developer
        """,
        file_name="sample.pdf",
    )

    assert parsed["file_name"] == "sample.pdf"
    assert parsed["email"] == "raul@example.com"
    assert parsed["skills"] is not None


def test_extract_resume_data_handles_missing_fields_gracefully():
    parsed = extract_resume_data(
        """
        This CV has almost no structured information.
        Only random text.
        """,
        file_name="weak_cv.pdf",
    )

    assert parsed["file_name"] == "weak_cv.pdf"
    assert "email" in parsed
    assert "phone" in parsed
    assert "skills" in parsed


def test_extract_resume_data_detects_skills_section():
    parsed = extract_resume_data(
        """
        Skills
        Python, JavaScript, SQL, React
        """,
        file_name="skills_cv.pdf",
    )

    skills_text = str(parsed["skills"]).lower()
    assert "python" in skills_text
    assert "sql" in skills_text


def test_extract_resume_data_keeps_source_file_name():
    parsed = extract_resume_data("test content", file_name="my_cv.pdf")
    assert parsed["file_name"] == "my_cv.pdf"
    
def test_parser_handles_noisy_text():
    parsed = extract_resume_data(
        "random text without structure 123 !!!",
        file_name="noisy.pdf",
    )
    assert parsed["file_name"] == "noisy.pdf"