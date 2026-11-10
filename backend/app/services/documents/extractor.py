from dataclasses import dataclass, field
from pathlib import Path
import re

import pdfplumber

from backend.app.services.documents.chunking import build_chunks


KNOWN_SECTIONS = {
    "abstract", "introduction", "background", "related work", "literature review", "methodology",
    "methods", "materials and methods", "experimental setup", "experiments", "results", "discussion",
    "results and discussion", "conclusion", "conclusions", "limitations", "future work", "references",
    "bibliography", "acknowledgments", "acknowledgements",
}
DOI_PATTERN = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
YEAR_PATTERN = re.compile(r"\b(19\d{2}|20\d{2})\b")


@dataclass
class ExtractedPage:
    page_number: int
    text: str = ""
    section_heading: str | None = None
    extraction_method: str = "text"
    warnings: list[str] = field(default_factory=list)


@dataclass
class ExtractedPaper:
    pages: list[ExtractedPage]
    chunks: list[dict[str, object]]
    metadata: dict[str, object]
    metadata_sources: dict[str, str]
    warnings: list[str]


def _normalize_metadata(value: object) -> str | None:
    if value is None:
        return None
    result = str(value).strip()
    if not result or result.lower() in {"none", "unknown", "untitled"}:
        return None
    return result


def _find_abstract(front_text: str) -> str | None:
    match = re.search(
        r"(?:^|\n)\s*abstract\s*(?:\n|[:\u2013\u2014-]\s*)(.*?)(?=\n\s*(?:keywords?|index terms|\d+\.?\s+introduction|introduction|background)\b|\Z)",
        front_text,
        re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return None
    abstract = re.sub(r"\s+", " ", match.group(1)).strip()
    return abstract[:12000] or None


def _is_heading(line: str) -> str | None:
    text = re.sub(r"\s+", " ", line).strip().strip(".:—–-")
    if len(text) > 100 or not text:
        return None
    normalized = re.sub(r"^\d+(?:\.\d+)*\s*", "", text).strip().lower()
    if normalized in KNOWN_SECTIONS:
        return text
    return None


def _ocr_page(page: pdfplumber.page.Page) -> str:
    import pytesseract

    image = page.to_image(resolution=220).original
    return pytesseract.image_to_string(image)


def extract_pdf(path: Path, ocr_enabled: bool = False) -> ExtractedPaper:
    pages: list[ExtractedPage] = []
    warnings: list[str] = []
    metadata: dict[str, object] = {}
    metadata_sources: dict[str, str] = {}

    try:
        with pdfplumber.open(path) as pdf:
            if not pdf.pages:
                raise ValueError("The PDF has no readable pages.")
            pdf_meta = pdf.metadata or {}
            prior_section: str | None = None
            for page_number, pdf_page in enumerate(pdf.pages, start=1):
                page_warnings: list[str] = []
                method = "text"
                try:
                    text = pdf_page.extract_text(x_tolerance=2, y_tolerance=3) or ""
                except Exception:
                    text = ""
                    page_warnings.append("Text extraction failed for this page.")

                try:
                    tables = pdf_page.extract_tables() or []
                    table_text = [" | ".join(str(cell or "").strip() for cell in row) for table in tables for row in table]
                    if table_text:
                        text = f"{text}\n\n[Extracted table]\n" + "\n".join(table_text)
                except Exception:
                    page_warnings.append("Table extraction failed for this page; extracted page text was retained.")

                if len(re.sub(r"\s", "", text)) < 25:
                    if ocr_enabled:
                        try:
                            ocr_text = _ocr_page(pdf_page).strip()
                            if len(re.sub(r"\s", "", ocr_text)) >= 25:
                                text = ocr_text
                                method = "ocr"
                            else:
                                page_warnings.append("OCR ran but did not find readable text.")
                        except ImportError:
                            page_warnings.append("OCR is enabled but the optional pytesseract package is not installed.")
                        except Exception:
                            page_warnings.append("OCR could not process this page; check that Tesseract OCR is installed.")
                    else:
                        page_warnings.append("No selectable text was found; OCR is disabled.")

                for line in text.splitlines():
                    heading = _is_heading(line)
                    if heading:
                        prior_section = heading
                if page_number == 1 and prior_section == "Abstract":
                    # Preserve the conventional abstract section label for the first page.
                    section = prior_section
                else:
                    section = prior_section
                pages.append(ExtractedPage(page_number, text.strip(), section, method, page_warnings))
                warnings.extend(f"Page {page_number}: {item}" for item in page_warnings)

            front_text = "\n".join(page.text for page in pages[:3])
            full_text = "\n".join(page.text for page in pages)

            title = _normalize_metadata(pdf_meta.get("Title"))
            metadata_sources["title"] = "pdf_metadata" if title else "not_found"

            author_value = _normalize_metadata(pdf_meta.get("Author"))
            authors = [part.strip() for part in re.split(r"\s*[;|]\s*", author_value) if part.strip()] if author_value else []
            metadata_sources["authors"] = "pdf_metadata" if authors else "not_found"

            abstract = _find_abstract(front_text)
            metadata_sources["abstract"] = "page_text" if abstract else "not_found"

            # PDF CreationDate is the PDF file's metadata date, not necessarily its publication year.
            year = None
            metadata_sources["publication_year"] = "not_found"

            keyword_value = _normalize_metadata(pdf_meta.get("Keywords"))
            if not keyword_value:
                keyword_match = re.search(r"(?:keywords?|index terms)\s*[:\u2013\u2014-]\s*([^\n]{1,500})", front_text, re.IGNORECASE)
                keyword_value = keyword_match.group(1) if keyword_match else None
            keywords = [part.strip() for part in re.split(r"[,;]", keyword_value) if part.strip()] if keyword_value else []
            metadata_sources["keywords"] = "pdf_metadata" if _normalize_metadata(pdf_meta.get("Keywords")) else "page_text" if keywords else "not_found"

            doi_match = DOI_PATTERN.search(front_text)
            doi = doi_match.group(0).rstrip(".,;)") if doi_match else None
            metadata_sources["doi"] = "page_text" if doi else "not_found"

            references: list[str] = []
            reference_match = re.search(r"(?:^|\n)\s*(?:references|bibliography)\s*(?:\n|$)(.*)\Z", full_text, re.IGNORECASE | re.DOTALL)
            if reference_match:
                references = [line.strip() for line in reference_match.group(1).splitlines() if len(line.strip()) > 12][:200]
            metadata_sources["references"] = "page_text" if references else "not_found"

            if not title:
                # Keep the heuristic explicit; callers can distinguish it from PDF metadata.
                candidate = next((line.strip() for line in (pages[0].text.splitlines() if pages else []) if 8 <= len(line.strip()) <= 250), None)
                if candidate and not _is_heading(candidate):
                    title = candidate
                    metadata_sources["title"] = "first_page_heuristic"

            if not year:
                candidate_year = next((int(value) for value in YEAR_PATTERN.findall(pages[0].text[:3000] if pages else "") if 1900 <= int(value) <= 2100), None)
                if candidate_year:
                    year = candidate_year
                    metadata_sources["publication_year"] = "first_page_heuristic"

            chunks = build_chunks((page.page_number, page.text, page.section_heading) for page in pages)
            metadata = {
                "title": title,
                "authors": authors,
                "abstract": abstract,
                "publication_year": year,
                "doi": doi,
                "keywords": keywords,
                "references": references,
            }
            return ExtractedPaper(pages, chunks, metadata, metadata_sources, warnings)
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("The PDF could not be read. It may be damaged, encrypted, or unsupported.") from exc
