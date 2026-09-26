"""Build a timestamped PDF from pytest's JSON coverage and captured log."""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def main() -> None:
    coverage_path, log_path, output_path, timestamp, exit_code = sys.argv[1:]
    coverage = json.loads(Path(coverage_path).read_text(encoding="utf-8"))
    log_bytes = Path(log_path).read_bytes()
    if log_bytes.startswith((b"\xff\xfe", b"\xfe\xff")):
        log = log_bytes.decode("utf-16")
    elif log_bytes.count(b"\x00") > len(log_bytes) // 8:
        log = log_bytes.decode("utf-16-le")
    else:
        log = log_bytes.decode("utf-8-sig", errors="replace")
    totals = coverage["totals"]

    summary_match = re.search(r"(\d+\s+passed[^\r\n]*)", log)
    test_summary = summary_match.group(1).strip() if summary_match else "Summary unavailable"
    passed_match = re.search(r"(\d+) passed", test_summary)
    failed_match = re.search(r"(\d+) failed", test_summary)
    passed = int(passed_match.group(1)) if passed_match else 0
    failed = int(failed_match.group(1)) if failed_match else 0
    warning_match = re.search(r"(\d+) warnings?", test_summary)
    warning_count = int(warning_match.group(1)) if warning_match else 0
    result = "PASSED" if exit_code == "0" and failed == 0 and totals["percent_covered"] >= 90 else "FAILED"

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportTitle", parent=styles["Title"], alignment=TA_CENTER,
        textColor=colors.HexColor("#17365D"), spaceAfter=10,
    ))
    styles.add(ParagraphStyle(
        name="Section", parent=styles["Heading2"], textColor=colors.HexColor("#17365D"),
        spaceBefore=12, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(name="SmallBody", parent=styles["BodyText"], fontSize=8, leading=10))

    document = SimpleDocTemplate(
        output_path, pagesize=landscape(letter), rightMargin=0.55*inch,
        leftMargin=0.55*inch, topMargin=0.5*inch, bottomMargin=0.5*inch,
        title=f"Test and Coverage Report {timestamp}", author="Automated Test Run",
    )
    story = [
        Paragraph("Automated Test &amp; Code Coverage Report", styles["ReportTitle"]),
        Paragraph(
            f"Generated: {datetime.strptime(timestamp, '%Y%m%d_%H%M%S').strftime('%Y-%m-%d %H:%M:%S')}",
            styles["Normal"],
        ),
        Paragraph("Environment profile: test (APP_ENV=test)", styles["Normal"]),
        Paragraph("Run Summary", styles["Section"]),
    ]

    summary = [
        ["Result", result, "Passed", str(passed), "Failed", str(failed)],
        ["Total coverage", f"{totals['percent_covered']:.2f}%", "Minimum", "90%", "Warnings", str(warning_count)],
    ]
    summary_table = Table(summary, colWidths=[1.1*inch, 1.1*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EAF0F7")),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#EAF0F7")),
        ("BACKGROUND", (4, 0), (4, -1), colors.HexColor("#EAF0F7")),
        ("TEXTCOLOR", (1, 0), (1, 0), colors.HexColor("#18794E") if result == "PASSED" else colors.red),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B7C9D6")),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([
        summary_table,
        Spacer(1, 8),
        Paragraph(f"Pytest result: {test_summary}", styles["SmallBody"]),
        Paragraph("Coverage scope: backend and config modules; the Streamlit frontend is excluded.", styles["SmallBody"]),
        Paragraph("Coverage threshold is enforced by pytest.ini.", styles["SmallBody"]),
        Paragraph("Per-Module Coverage", styles["Section"]),
    ])

    rows = [["Module", "Statements", "Missed", "Coverage"]]
    for filename, details in sorted(coverage["files"].items()):
        module_summary = details["summary"]
        rows.append([
            filename.replace("\\", "/"),
            str(module_summary["num_statements"]),
            str(module_summary["missing_lines"]),
            f"{module_summary['percent_covered']:.2f}%",
        ])
    rows.append([
        "TOTAL", str(totals["num_statements"]), str(totals["missing_lines"]),
        f"{totals['percent_covered']:.2f}%",
    ])
    coverage_table = Table(rows, repeatRows=1, colWidths=[4.5*inch, 1.25*inch, 1.0*inch, 1.0*inch])
    coverage_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17365D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#EAF0F7")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B7C9D6")),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.extend([
        coverage_table,
        Spacer(1, 10),
        Paragraph("The matching timestamped .log and .json files contain the captured run output and machine-readable coverage data.", styles["SmallBody"]),
    ])
    document.build(story)
    print(f"Created: {Path(output_path).resolve()}")
    print(f"Result: {result}; {test_summary}; coverage {totals['percent_covered']:.2f}%")


if __name__ == "__main__":
    main()
