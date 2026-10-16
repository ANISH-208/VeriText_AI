from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _highlighted(text: str, ranges: list[dict]) -> str:
    valid = sorted(
        (r for r in ranges if isinstance(r, dict) and isinstance(r.get("start"), int) and isinstance(r.get("end"), int)
         and 0 <= r["start"] < r["end"] <= len(text)), key=lambda r: r["start"]
    )
    pieces, cursor = [], 0
    for item in valid:
        start, end = max(cursor, item["start"]), item["end"]
        if start > cursor:
            pieces.append(escape(text[cursor:start]))
        if end > start:
            pieces.append(f'<font backColor="#fff0c8">{escape(text[start:end])}</font>')
            cursor = end
    pieces.append(escape(text[cursor:]))
    return "".join(pieces).replace("\n", "<br/>")


def create_pdf(report: dict) -> bytes:
    output = BytesIO()
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=8, leading=11, textColor=colors.HexColor("#596174"), spaceAfter=5))
    styles.add(ParagraphStyle(name="Evidence", parent=styles["BodyText"], fontSize=9, leading=13, alignment=TA_LEFT, borderColor=colors.HexColor("#e3e6ef"), borderWidth=.5, borderPadding=7, backColor=colors.HexColor("#fbfbfd"), spaceAfter=6))
    styles.add(ParagraphStyle(name="Subheading", parent=styles["Heading3"], fontSize=11, leading=14, textColor=colors.HexColor("#333b5c"), spaceBefore=7, spaceAfter=5))
    doc = SimpleDocTemplate(output, pagesize=letter, rightMargin=.65 * inch, leftMargin=.65 * inch, topMargin=.62 * inch, bottomMargin=.62 * inch, title="VeriText AI Analysis Report")
    story = [Paragraph("VeriText AI — Analysis Report", styles["Title"]),
             Paragraph("Similarity indicators for human review. This report does not determine plagiarism or misconduct.", styles["Small"]), Spacer(1, 8)]
    metrics = report.get("metrics", {})
    rows = [["Measure", "Result"],
            ["Submitted words", str(report.get("submitted_word_count", "—"))],
            ["Matched text coverage", "N/A (no references)" if metrics.get("matched_text_coverage") is None else f'{metrics.get("matched_text_coverage")}%'],
            ["Flagged passages", str(metrics.get("matched_passage_count", 0))],
            ["Mean lexical signal", str(metrics.get("mean_lexical_similarity", "—"))],
            ["Mean semantic signal", str(metrics.get("mean_semantic_similarity", "Unavailable"))]]
    table = Table(rows, colWidths=[2.5 * inch, 4.5 * inch], repeatRows=1)
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef0ff")),
                               ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#424d96")),
                               ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                               ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#e3e6ef")),
                               ("FONTSIZE", (0, 0), (-1, -1), 9),
                               ("VALIGN", (0, 0), (-1, -1), "TOP"),
                               ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                               ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    story.extend([table, Spacer(1, 12)])

    citations = report.get("citations", {})
    if citations:
        story.append(Paragraph("Source citation suggestions", styles["Heading2"]))
        for filename, citation in citations.items():
            formatted = citation.get("formatted") or filename
            story.append(Paragraph(f"<b>{escape(filename)}</b><br/>{escape(formatted)}", styles["Small"]))

    story.append(Paragraph("Passage evidence", styles["Heading2"]))
    for index, match in enumerate(report.get("matches", []), start=1):
        source = escape(str(match.get("reference_name", "Source")))
        source_page = match.get("reference_page")
        submitted_page = match.get("submitted_page")
        status = escape(str(match.get("review_status", "to_review"))).replace("_", " ").title()
        heading = f'{index}. {escape(str(match.get("category", "match")).replace("_", " ").title())} — {source}'
        if source_page:
            heading += f" (source p. {source_page})"
        if submitted_page:
            heading += f" · submitted p. {submitted_page}"
        story.append(Paragraph(heading, styles["Subheading"]))
        story.append(Paragraph(f"Review: {status} · Lexical {float(match.get('lexical_score', 0)):.0%} · Semantic {float(match.get('semantic_score', 0)):.0%} · {escape(str(match.get('detection_method', '')))}", styles["Small"]))
        story.append(Paragraph("Submitted passage", styles["Small"]))
        story.append(Paragraph(_highlighted(str(match.get("submitted_passage", "")), match.get("submitted_highlights", [])), styles["Evidence"]))
        story.append(Paragraph("Reference passage", styles["Small"]))
        story.append(Paragraph(_highlighted(str(match.get("reference_passage", "")), match.get("reference_highlights", [])), styles["Evidence"]))
        if match.get("review_note"):
            story.append(Paragraph(f"<b>Reviewer note:</b> {escape(str(match['review_note']))}", styles["Small"]))

    story.extend([Spacer(1, 8), Paragraph("Interpretation and limitations", styles["Heading2"])])
    story.append(Paragraph(escape(report.get("ai_writing_signals", {}).get("disclaimer", "Writing-pattern signals are exploratory.")), styles["Small"]))
    for limitation in report.get("limitations", []):
        story.append(Paragraph(f"• {escape(str(limitation))}", styles["Small"]))

    def footer(canvas, _doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#858b99"))
        canvas.drawString(.65 * inch, .34 * inch, "VeriText AI · For human review")
        canvas.drawRightString(7.85 * inch, .34 * inch, f"Page {_doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()
