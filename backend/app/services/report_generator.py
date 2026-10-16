from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def create_pdf(report: dict) -> bytes:
    output = BytesIO(); c = canvas.Canvas(output, pagesize=letter); width, height = letter
    y = height - 48
    def line(text, size=10):
        nonlocal y
        if y < 55:
            c.showPage(); y = height - 48
        safe = text.encode("latin-1", "replace").decode("latin-1")
        c.setFont("Helvetica", size); c.drawString(48, y, safe[:110]); y -= size + 7
    line("VeriText AI — Analysis Report", 16)
    line("Similarity indicators for human review. This report does not determine misconduct.")
    m = report.get("metrics", {})
    for label, key in [("Matched text coverage (%)", "matched_text_coverage"), ("Mean lexical similarity", "mean_lexical_similarity"), ("Maximum lexical similarity", "max_lexical_similarity"), ("Mean semantic similarity", "mean_semantic_similarity"), ("Maximum semantic similarity", "max_semantic_similarity"), ("Matched passages", "matched_passage_count")]:
        value = m.get(key); line(f"{label}: {'N/A (no references)' if value is None else value}")
    line("Passage matches", 13)
    for match in report.get("matches", []):
        line(f"[{match['category']}] {match['reference_name']} | lexical {match['lexical_score']:.2f} | semantic {match['semantic_score']:.2f}")
        line("Submitted: " + match["submitted_passage"])
        line("Source: " + match["reference_passage"])
    line("Experimental writing-pattern signals", 13)
    line(report.get("ai_writing_signals", {}).get("disclaimer", ""))
    c.save(); return output.getvalue()
