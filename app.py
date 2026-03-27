from __future__ import annotations

import io

import pandas as pd
import streamlit as st

from config import (
    ALLOWED_UPLOAD_TYPES,
    APP_TITLE,
    DEFAULT_OUTPUT_FILENAME,
    MAX_UPLOAD_SIZE_MB,
)
from read_pdf_csv import extract_resume_data, extract_text_from_pdf_bytes


st.set_page_config(page_title=APP_TITLE, layout="centered")
st.title(APP_TITLE)
st.caption("Upload a CV (PDF), then click Parse CV to see extracted text and parsed fields.")

uploaded_file = st.file_uploader(
    "Click to upload CV",
    type=ALLOWED_UPLOAD_TYPES,
    accept_multiple_files=False,
)

if uploaded_file is None:
    st.info("No CV selected yet.")
else:
    st.success(f"CV selected: {uploaded_file.name}")

    if uploaded_file.size > MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        st.error(
            f"File is too large ({uploaded_file.size / (1024 * 1024):.2f} MB). "
            f"Maximum allowed is {MAX_UPLOAD_SIZE_MB} MB."
        )
    else:
        parse_clicked = st.button("Parse CV", type="primary")

        if parse_clicked:
            with st.spinner("Parsing CV..."):
                pdf_bytes = uploaded_file.read()
                extracted_text = extract_text_from_pdf_bytes(pdf_bytes)
                parsed_resume = extract_resume_data(extracted_text, file_name=uploaded_file.name)

            st.subheader("Output Text")
            if extracted_text.strip():
                st.text_area(
                    "Extracted PDF Text",
                    extracted_text,
                    height=280,
                )
            else:
                st.warning("No extractable text was found in this PDF.")

            st.subheader("Parsed Fields")
            st.json(parsed_resume)

            output_row = {
                key: "; ".join(value) if isinstance(value, list) else (value or "")
                for key, value in parsed_resume.items()
            }
            output_df = pd.DataFrame([output_row])

            csv_buffer = io.StringIO()
            output_df.to_csv(csv_buffer, index=False)
            st.download_button(
                "Download Parsed CSV",
                data=csv_buffer.getvalue(),
                file_name=DEFAULT_OUTPUT_FILENAME,
                mime="text/csv",
            )
