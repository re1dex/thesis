# Parser Evaluation

## Overview

This section presents a small evaluation of the resume parser used in the **Automated Job Market Scout** system.

The goal of this evaluation is to demonstrate how well the system extracts key information from CVs and to analyze how CV structure affects machine readability.

---

## Evaluation Setup

The parser was tested on a small set of real CVs with different structures and formatting styles. The evaluation focuses on the extraction of the following fields:

* Name
* Email
* Phone
* Skills

Each field is marked as:

* **yes** → correctly extracted
* **no** → missing or incorrectly extracted

The results are stored in:

```
evaluation/parser_evaluation.csv
```

---

## Results Summary

The evaluation shows that the parser is able to successfully extract key fields from all tested CVs.

Structured CVs with clearly defined sections (such as *Skills*, *Experience*, and *Contact Information*) produce the most reliable results.

CVs that follow a consistent layout allow the parser to correctly identify and extract:

* contact details (email and phone),
* personal information (name),
* technical skills.

---

## Discussion

The results highlight an important insight:

> CV structure has a direct impact on machine readability.

Even when all fields are successfully extracted, differences in formatting quality affect extraction reliability and consistency.

For example:

* CVs with clear section headings and simple layouts are parsed more accurately.
* CVs with dense text or less structured formatting may still be parsed, but with lower confidence or increased risk of errors.

This confirms the main thesis argument that:

> A CV that looks visually well-designed is not always optimized for machine processing.

---

## Limitations

This evaluation is intentionally small and is not intended to be a large-scale benchmark.

The system has the following limitations:

* Performance may decrease on highly unstructured or unconventional CV formats.
* Complex layouts (multi-column, graphics-heavy designs) may affect extraction accuracy.
* The parser does not fully replicate the behavior of industrial ATS systems.

---

## Conclusion

The evaluation demonstrates that the parser performs reliably on structured CVs and is suitable for supporting job discovery.

More importantly, the system provides practical value by helping users understand how machine-readable their CV is and which parts may require improvement.
