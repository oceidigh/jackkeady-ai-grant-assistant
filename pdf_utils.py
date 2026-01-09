from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from io import BytesIO
import textwrap


def draw_wrapped_text(c, text, x, y, max_width=90, line_height=14):
    """
    Draw wrapped text line-by-line onto a PDF canvas.
    max_width is approx characters per line (PDF has no layout engine).
    """
    lines = []
    for paragraph in text.split("\n"):
        lines.extend(textwrap.wrap(paragraph, max_width))
        lines.append("")

    for line in lines:
        c.drawString(x, y, line)
        y -= line_height

    return y


def fill_application_pdf(template_path, output_path, answers, field_map):
    reader = PdfReader(template_path)
    writer = PdfWriter()

    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)

    current_page = 0

    for key, cfg in field_map.items():
        target_page = cfg["page"]

        while current_page < target_page:
            c.showPage()
            current_page += 1

        draw_wrapped_text(
            c,
            answers.get(key, ""),
            x=cfg["x"],
            y=cfg["y"],
            max_width=95,
            line_height=14
        )

    c.save()
    packet.seek(0)

    overlay = PdfReader(packet)

    for i, page in enumerate(reader.pages):
        if i < len(overlay.pages):
            page.merge_page(overlay.pages[i])
        writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)
