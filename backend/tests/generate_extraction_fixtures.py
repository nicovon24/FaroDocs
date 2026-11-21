"""Generate original, synthetic samples for parser and locator checks."""

from pathlib import Path

from docx import Document
from reportlab.pdfgen import canvas


def generate(target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    sample = "FaroDocs synthetic policy.\n\nThe review date is 2026-12-01.\n"
    (target / "sample.txt").write_text(sample, encoding="utf-8")
    (target / "sample.md").write_text("# Synthetic policy\n\nThe review date is 2026-12-01.\n", encoding="utf-8")
    word = Document()
    word.add_paragraph("FaroDocs synthetic policy.")
    word.add_paragraph("The review date is 2026-12-01.")
    table = word.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "Owner"
    table.cell(0, 1).text = "Local fixture"
    word.save(target / "sample.docx")
    pdf = canvas.Canvas(str(target / "sample.pdf"))
    pdf.drawString(72, 720, "FaroDocs synthetic policy.")
    pdf.showPage()
    pdf.drawString(72, 720, "The review date is 2026-12-01.")
    pdf.save()


if __name__ == "__main__":
    generate(Path("backend/tests/generated"))
