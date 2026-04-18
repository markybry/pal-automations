"""
Generate staff documents from Word templates for each house, organised by month.

Templates folder: ./Templates/
Output folder:    ./output/<house>/<Month YYYY>/

Placeholders replaced:
  {{house}}   - house name (e.g. "19 Bransley")
  {{date}}    - for weekly docs: date of the Monday (DD/MM/YYYY in doc,
                DD-MM-YYYY in filename); for monthly docs: month name (e.g. April)
                In the Weekly Shiftplan each table's {{date}} is replaced with
                the correct date for that day (Mon–Sun).
  {{weekNum}} - week number within the month (1, 2, 3, or 4)

The script checks each house's output folder for existing month folders
(named "Month YYYY", e.g. "April 2026") and generates the next missing month.

Usage:
    python createStaffDocs.py [--start DD/MM/YYYY] [--months N]

    --start   Any date in the first month to generate (defaults to auto-detect
              from output folder, or current month if output is empty).
    --months  Number of months to generate (default: 1).
"""

import calendar
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


def get_mondays_in_month(year: int, month: int) -> list:
    """Return all Mondays whose date falls within the given month."""
    _, last_day = calendar.monthrange(year, month)
    return [
        datetime(year, month, day)
        for day in range(1, last_day + 1)
        if datetime(year, month, day).weekday() == 0
    ]


def next_month(year: int, month: int) -> tuple:
    """Return (year, month) for the month following the given one."""
    return (year + 1, 1) if month == 12 else (year, month + 1)


def get_existing_month_folders(house_dir: str) -> set:
    """Return set of (year, month) tuples for existing 'Month YYYY' subfolders."""
    existing = set()
    if os.path.isdir(house_dir):
        for name in os.listdir(house_dir):
            try:
                dt = datetime.strptime(name, "%B %Y")
                existing.add((dt.year, dt.month))
            except ValueError:
                pass
    return existing


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
        description="Generate staff documents organised by month for each house."
    )
    parser.add_argument(
        "--start",
        type=str,
        default=None,
        help=(
            "Any date (DD/MM/YYYY) in the first month to generate. "
            "Defaults to auto-detecting the next missing month from the output folder, "
            "or the current month if the output folder is empty."
        ),
    )
    parser.add_argument(
        "--months",
        type=int,
        default=1,
        help="Number of months to generate (default: 1).",
    )
    args = parser.parse_args()

    templates = [f for f in os.listdir(TEMPLATES_DIR) if f.lower().endswith(".docx")]
    if not templates:
        print(f"No .docx templates found in: {TEMPLATES_DIR}")
        sys.exit(1)

    forced_start = None
    if args.start:
        try:
            base = datetime.strptime(args.start, "%d/%m/%Y")
            forced_start = (base.year, base.month)
        except ValueError:
            print("Invalid date format. Use DD/MM/YYYY.")
            sys.exit(1)

    today = datetime.today()
    print(f"Templates: {templates}")
    print(f"Houses:    {HOUSES}")
    print()

    total = 0
    for house in HOUSES:
        house_dir = os.path.join(OUTPUT_DIR, house)
        os.makedirs(house_dir, exist_ok=True)

        # Determine which month to start from
        if forced_start:
            start_year, start_month = forced_start
        else:
            existing = get_existing_month_folders(house_dir)
            if existing:
                start_year, start_month = next_month(*max(existing))
            else:
                start_year, start_month = today.year, today.month

        cur_year, cur_month = start_year, start_month
        for _ in range(args.months):
            month_label = datetime(cur_year, cur_month, 1).strftime("%B %Y")
            month_display = datetime(cur_year, cur_month, 1).strftime("%B")
            month_dir = os.path.join(house_dir, month_label)

            print(f"{house} — {month_label}")
            os.makedirs(month_dir, exist_ok=True)

            mondays = get_mondays_in_month(cur_year, cur_month)

            for template_name in templates:
                is_monthly = "Monthly" in template_name
                is_task_sheet = template_name.startswith("Task Sheet")
                house_number = house.split()[0]

                # Skip templates that belong to a different house
                if is_task_sheet and house_number not in template_name:
                    continue
                if is_monthly and not template_name.startswith(house_number):
                    continue

                template_path = os.path.join(TEMPLATES_DIR, template_name)

                if is_monthly:
                    # One file per month; {{date}} = month name
                    doc_repl = {
                        "{{house}}": house,
                        "{{date}}": month_display,
                        "{{weekNum}}": "",
                    }
                    output_name = template_name
                    for ph, val in doc_repl.items():
                        output_name = output_name.replace(ph, val)

                    sub_dir = os.path.join(month_dir, "Task Sheets")
                    os.makedirs(sub_dir, exist_ok=True)
                    output_path = os.path.join(sub_dir, output_name)

                    doc = Document(template_path)
                    replace_in_doc(doc, doc_repl)
                    doc.save(output_path)

                    rel = os.path.relpath(output_path, OUTPUT_DIR)
                    print(f"  Created: {rel}")
                    total += 1

                else:
                    # One file per Monday in the month
                    for week_monday in mondays:
                        week_num = week_of_month(week_monday)
                        date_filename = week_monday.strftime("%d-%m-%Y")
                        date_disp = week_monday.strftime("%d/%m/%Y")

                        doc_repl = {
                            "{{house}}": house,
                            "{{date}}": date_disp,
                            "{{weekNum}}": str(week_num),
                        }
                        name_repl = {
                            "{{house}}": house,
                            "{{date}}": date_filename,
                            "{{weekNum}}": str(week_num),
                        }

                        output_name = template_name
                        for ph, val in name_repl.items():
                            output_name = output_name.replace(ph, val)

                        sub_dir = os.path.join(
                            month_dir,
                            "Task Sheets" if is_task_sheet else "Weekly Shiftplans",
                        )
                        os.makedirs(sub_dir, exist_ok=True)
                        output_path = os.path.join(sub_dir, output_name)

                        doc = Document(template_path)
                        if template_name.startswith("Weekly Shiftplan"):
                            replace_in_shiftplan_doc(doc, week_monday, doc_repl)
                        else:
                            replace_in_doc(doc, doc_repl)
                        doc.save(output_path)

                        rel = os.path.relpath(output_path, OUTPUT_DIR)
                        print(f"  Created: {rel}")
                        total += 1

            cur_year, cur_month = next_month(cur_year, cur_month)

    print(f"\nDone — {total} files created in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
