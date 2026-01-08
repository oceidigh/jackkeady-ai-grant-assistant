import io
import textwrap
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from pypdf import PdfReader, PdfWriter

def fill_application_pdf(template_path, output_path, answers, field_map):
    reader = PdfReader(template_path)
    writer = PdfWriter()

    for page_index, page in enumerate(reader.pages):
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=A4)
        can.setFont("Helvetica", 9)

        for field, cfg in field_map.items():
            if cfg["page"] == page_index and field in answers:
                wrapped = textwrap.wrap(answers[field], 90)
                y = cfg["y"]

                for line in wrapped:
                    can.drawString(cfg["x"], y, line)
                    y -= 11

        can.save()
        packet.seek(0)

        overlay = PdfReader(packet).pages[0]
        page.merge_page(overlay)
        writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)
