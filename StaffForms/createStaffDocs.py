"""
Generate staff documents from Word templates for each week and house.

Templates folder: ./Templates/
Output folder:    ./output/<house>/

Placeholders replaced:
  {{house}}   - house name (e.g. "19 Bransley")
  {{date}}    - date for each day (DD/MM/YYYY in doc, DD-MM-YYYY in filename)
                In the Weekly Shiftplan each table's {{date}} is replaced with
                the correct date for that day (Mon–Sun).
  {{weekNum}} - week number within the month (1, 2, 3, or 4)

Usage:
    python createStaffDocs.py [--start DD/MM/YYYY] [--weeks N]

    --start   First week's Monday date (defaults to this week's Monday)
    --weeks   Number of weeks to generate (default: 4)
"""

import os
import sys
import argparse
from datetime import datetime, timedelta

try:
    from docx import Document
except ImportError:
    print("python-docx not installed. Run: pip install python-docx")
    sys.exit(1)

HOUSES = ["19 Bransley", "17 Bransley"]
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")
TEMPLATES_DIR = os.path.join(SCRIPT_DIR, "Templates")


def get_monday(date: datetime) -> datetime:
    """Return the Monday of the week containing date."""
    return date - timedelta(days=date.weekday())


def week_of_month(monday: datetime) -> int:
    """Return which week of the month the given Monday falls in (1, 2, 3, or 4)."""
    return (monday.day - 1) // 7 + 1


def replace_in_paragraph(paragraph, replacements: dict) -> None:
    """
    Replace placeholders in a paragraph.

    Tries per-run replacement first (preserves run formatting).
    Falls back to joining all runs into the first run when a placeholder
    is split across multiple runs.
    """
    # Pass 1: replace within individual runs
    for run in paragraph.runs:
        for placeholder, value in replacements.items():
            if placeholder in run.text:
                run.text = run.text.replace(placeholder, value)

    # Pass 2: check if any placeholder survived (split across runs)
    full_text = "".join(run.text for run in paragraph.runs)
    if any(ph in full_text for ph in replacements):
        new_text = full_text
        for placeholder, value in replacements.items():
            new_text = new_text.replace(placeholder, value)
        if paragraph.runs:
            paragraph.runs[0].text = new_text
            for run in paragraph.runs[1:]:
                run.text = ""


def _replace_headers_footers(doc: "Document", replacements: dict) -> None:
    """Replace placeholders in all headers and footers of a document."""
    for section in doc.sections:
        for part in (
            section.header,
            section.footer,
            section.even_page_header,
            section.even_page_footer,
            section.first_page_header,
            section.first_page_footer,
        ):
            if part is not None:
                for paragraph in part.paragraphs:
                    replace_in_paragraph(paragraph, replacements)
                for table in part.tables:
                    for row in table.rows:
                        for cell in row.cells:
                            for paragraph in cell.paragraphs:
                                replace_in_paragraph(paragraph, replacements)


def replace_in_doc(doc: "Document", replacements: dict) -> None:
    """Replace placeholders throughout the entire document."""
    # Body paragraphs
    for paragraph in doc.paragraphs:
        replace_in_paragraph(paragraph, replacements)

    # Tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    replace_in_paragraph(paragraph, replacements)

    _replace_headers_footers(doc, replacements)


def replace_in_shiftplan_doc(
    doc: "Document", week_monday: datetime, base_replacements: dict
) -> None:
    """
    Process a Weekly Shiftplan document.

    The document contains 7 tables (index 0-6) corresponding to Mon-Sun.
    Each table's {{date}} placeholder is replaced with the actual date for
    that day; all other placeholders use base_replacements.
    """
    # Body paragraphs (no {{date}} in this template's body)
    for paragraph in doc.paragraphs:
        replace_in_paragraph(paragraph, base_replacements)

    for i, table in enumerate(doc.tables):
        if i < 7:
            day_date = week_monday + timedelta(days=i)
            table_replacements = {
                **base_replacements,
                "{{date}}": day_date.strftime("%d/%m/%Y"),
            }
        else:
            table_replacements = base_replacements

        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    replace_in_paragraph(paragraph, table_replacements)

    _replace_headers_footers(doc, base_replacements)


def main():
    parser = argparse.ArgumentParser(
        description="Generate staff documents for each week and house."
    )
    parser.add_argument(
        "--start",
        type=str,
        default=None,
        help="Start date as DD/MM/YYYY (defaults to this week's Monday).",
    )
    parser.add_argument(
        "--weeks",
        type=int,
        default=4,
        help="Number of weeks to generate (default: 4).",
    )
    args = parser.parse_args()

    if args.start:
        try:
            base = datetime.strptime(args.start, "%d/%m/%Y")
        except ValueError:
            print("Invalid date format. Use DD/MM/YYYY.")
            sys.exit(1)
        monday = get_monday(base)
    else:
        monday = get_monday(datetime.today())

    templates = [f for f in os.listdir(TEMPLATES_DIR) if f.lower().endswith(".docx")]
    if not templates:
        print(f"No .docx templates found in: {TEMPLATES_DIR}")
        sys.exit(1)

    print(f"Templates:  {templates}")
    print(f"Start week: {monday.strftime('%d/%m/%Y')} (Monday)")
    print(f"Weeks:      {args.weeks}")
    print(f"Houses:     {HOUSES}")
    print()

    total = 0
    for house in HOUSES:
        house_dir = os.path.join(OUTPUT_DIR, house)
        os.makedirs(house_dir, exist_ok=True)

        for week_offset in range(args.weeks):
            week_monday = monday + timedelta(weeks=week_offset)
            week_num = week_of_month(week_monday)

            # Filename gets dashes (/ is invalid in Windows paths)
            date_filename = week_monday.strftime("%d-%m-%Y")
            # Document content gets the friendlier DD/MM/YYYY
            date_display = week_monday.strftime("%d/%m/%Y")

            doc_replacements = {
                "{{house}}": house,
                "{{date}}": date_display,
                "{{weekNum}}": str(week_num),
            }
            name_replacements = {
                "{{house}}": house,
                "{{date}}": date_filename,
                "{{weekNum}}": str(week_num),
            }

            for template_name in templates:
                template_path = os.path.join(TEMPLATES_DIR, template_name)

                # Build output filename from template name
                output_name = template_name
                for placeholder, value in name_replacements.items():
                    output_name = output_name.replace(placeholder, value)

                # Place into subfolder based on template type
                if template_name.startswith("Task Sheet"):
                    sub_dir = os.path.join(house_dir, "Task Sheets")
                else:
                    sub_dir = os.path.join(house_dir, "Weekly Shiftplans")
                os.makedirs(sub_dir, exist_ok=True)

                output_path = os.path.join(sub_dir, output_name)

                doc = Document(template_path)
                if template_name.startswith("Weekly Shiftplan"):
                    replace_in_shiftplan_doc(doc, week_monday, doc_replacements)
                else:
                    replace_in_doc(doc, doc_replacements)
                doc.save(output_path)

                rel = os.path.relpath(output_path, OUTPUT_DIR)
                print(f"  Created: {rel}")
                total += 1

    print(f"\nDone — {total} files created in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
