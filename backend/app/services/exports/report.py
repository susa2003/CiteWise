from io import BytesIO
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape


SKIP_FIELDS = {"id", "run_id", "document_id", "document_ids", "chunk_id", "score"}
HEADING_FIELDS = ("heading", "category", "title", "filename")


def _blocks(value: Any, depth: int = 0):
    if isinstance(value, list):
        for item in value:
            yield from _blocks(item, depth)
        return
    if isinstance(value, dict):
        heading = next((value.get(key) for key in HEADING_FIELDS if isinstance(value.get(key), str) and value.get(key).strip()), None)
        if heading:
            yield ("heading", str(heading), min(depth, 2))
        if isinstance(value.get("text"), str) and value["text"].strip():
            prefix = "Interpretation: " if value.get("interpretation") else ""
            yield ("paragraph", prefix + value["text"].strip(), depth)
        if isinstance(value.get("explanation"), str) and value["explanation"].strip():
            yield ("paragraph", value["explanation"].strip(), depth)
        sources = value.get("sources")
        if isinstance(sources, list):
            for source in sources:
                if not isinstance(source, dict):
                    continue
                file_name = str(source.get("filename", "Source paper"))
                page = source.get("page_number", "?")
                yield ("citation", f"Source: {file_name}, page {page}", depth)
                excerpt = source.get("excerpt")
                if excerpt:
                    yield ("quote", str(excerpt), depth)
        consumed = set(HEADING_FIELDS) | {"text", "interpretation", "explanation", "sources"} | SKIP_FIELDS
        for key, child in value.items():
            if key in consumed or child is None:
                continue
            if isinstance(child, (str, int, float, bool)):
                label = key.replace("_", " ").capitalize()
                yield ("detail", f"{label}: {child}", depth)
            elif isinstance(child, (dict, list)):
                yield from _blocks(child, depth + 1)
        return
    if isinstance(value, str) and value.strip():
        yield ("paragraph", value.strip(), depth)


def _report_title(kind: str) -> str:
    return f"CiteWise AI — {kind.replace('_', ' ').title()} Report"


def render_docx(kind: str, data: dict[str, Any]) -> bytes:
    from docx import Document as WordDocument
    from docx.shared import Inches, Pt, RGBColor

    document = WordDocument()
    section = document.sections[0]
    section.top_margin = Inches(0.75)
    section.bottom_margin = Inches(0.7)
    heading = document.add_heading(_report_title(kind), level=0)
    heading.runs[0].font.color.rgb = RGBColor(35, 91, 67)
    document.add_paragraph("Generated from a stored, evidence-linked CiteWise analysis.", style="Subtitle")
    for block_type, text, depth in _blocks(data):
        if block_type == "heading":
            document.add_heading(text, level=min(depth + 1, 3))
        elif block_type == "citation":
            paragraph = document.add_paragraph(style="Caption")
            paragraph.add_run(text).font.color.rgb = RGBColor(52, 112, 78)
        elif block_type == "quote":
            paragraph = document.add_paragraph(style="Quote")
            paragraph.add_run(text)
        elif block_type == "detail":
            document.add_paragraph(text, style="List Bullet" if depth > 0 else "Normal")
        else:
            document.add_paragraph(text)
    for paragraph in document.paragraphs:
        for run in paragraph.runs:
            run.font.name = "Aptos"
            run.font.size = Pt(10)
    output = BytesIO()
    document.save(output)
    return output.getvalue()


def render_pdf(kind: str, data: dict[str, Any]) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    output = BytesIO()
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("CiteWiseTitle", parent=styles["Title"], textColor=colors.HexColor("#245c43"), alignment=TA_LEFT, fontSize=20, leading=25, spaceAfter=8))
    styles.add(ParagraphStyle("CiteWiseHeading", parent=styles["Heading2"], textColor=colors.HexColor("#285c45"), fontSize=13, leading=17, spaceBefore=13, spaceAfter=5))
    styles.add(ParagraphStyle("CiteWiseDetail", parent=styles["BodyText"], leftIndent=12, fontSize=9, leading=13, textColor=colors.HexColor("#56635a"), spaceAfter=3))
    styles.add(ParagraphStyle("CiteWiseCitation", parent=styles["BodyText"], fontSize=8, leading=11, textColor=colors.HexColor("#36704e"), leftIndent=10, spaceBefore=3))
    styles.add(ParagraphStyle("CiteWiseQuote", parent=styles["BodyText"], fontSize=8, leading=11, textColor=colors.HexColor("#737f75"), leftIndent=18, borderColor=colors.HexColor("#dce7dd"), borderWidth=0.7, borderPadding=5, spaceAfter=5))
    story = [
        Paragraph(escape(_report_title(kind)), styles["CiteWiseTitle"]),
        Paragraph("Generated from a stored, evidence-linked CiteWise analysis.", styles["Italic"]),
        Spacer(1, 0.18 * inch),
    ]
    for block_type, text, depth in _blocks(data):
        safe_text = escape(text).replace("\n", "<br/>")
        if block_type == "heading":
            story.append(Paragraph(safe_text, styles["CiteWiseHeading"]))
        elif block_type == "citation":
            story.append(Paragraph(safe_text, styles["CiteWiseCitation"]))
        elif block_type == "quote":
            story.append(Paragraph(safe_text, styles["CiteWiseQuote"]))
        else:
            story.append(Paragraph(safe_text, styles["CiteWiseDetail" if block_type == "detail" else "BodyText"]))
        story.append(Spacer(1, 3))

    def draw_footer(canvas, _document):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#e4eae4"))
        canvas.line(0.75 * inch, 0.55 * inch, 7.75 * inch, 0.55 * inch)
        canvas.setFillColor(colors.HexColor("#7f8c82"))
        canvas.setFont("Helvetica", 8)
        canvas.drawString(0.75 * inch, 0.38 * inch, "CiteWise AI · Source evidence preserved")
        canvas.drawRightString(7.75 * inch, 0.38 * inch, f"Page {canvas.getPageNumber()}")
        canvas.restoreState()

    pdf = SimpleDocTemplate(
        output,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.8 * inch,
        title=_report_title(kind),
        author="CiteWise AI",
    )
    pdf.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)
    return output.getvalue()


def render_report(kind: str, data: dict[str, Any], output_format: str) -> bytes:
    if output_format == "pdf":
        return render_pdf(kind, data)
    if output_format == "docx":
        return render_docx(kind, data)
    raise ValueError("Unsupported report format")
