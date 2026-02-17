import base64
import io
import tempfile

import pikepdf
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas as rl_canvas


class PdfProcessor:
    @staticmethod
    def rotate_page(input_path: str, page_num: int, angle: int) -> str:
        """Rotate a single page by angle (90, 180, 270)."""
        pdf = pikepdf.Pdf.open(input_path)
        page = pdf.pages[page_num]
        page.rotate(angle, relative=True)
        out = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        pdf.save(out.name)
        pdf.close()
        return out.name

    @staticmethod
    def delete_page(input_path: str, page_num: int) -> str:
        pdf = pikepdf.Pdf.open(input_path)
        if len(pdf.pages) <= 1:
            pdf.close()
            raise ValueError("Cannot delete the only page")
        del pdf.pages[page_num]
        out = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        pdf.save(out.name)
        pdf.close()
        return out.name

    @staticmethod
    def reorder_pages(input_path: str, new_order: list[int]) -> str:
        """new_order is a list of 0-based page indices in desired order."""
        pdf = pikepdf.Pdf.open(input_path)
        new_pdf = pikepdf.Pdf.new()
        for idx in new_order:
            new_pdf.pages.append(pdf.pages[idx])
        out = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        new_pdf.save(out.name)
        new_pdf.close()
        pdf.close()
        return out.name

    @staticmethod
    def merge(input_paths: list[str]) -> str:
        new_pdf = pikepdf.Pdf.new()
        opened = []
        for path in input_paths:
            pdf = pikepdf.Pdf.open(path)
            opened.append(pdf)
            new_pdf.pages.extend(pdf.pages)
        out = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        new_pdf.save(out.name)
        new_pdf.close()
        for pdf in opened:
            pdf.close()
        return out.name

    @staticmethod
    def text_overlay(input_path: str, page_num: int, text: str, x: float, y: float,
                     font_size: float = 12, font_name: str = "Helvetica", color: tuple = (0, 0, 0)) -> str:
        """Add vector text via reportlab overlay, then stamp onto page with pikepdf."""
        pdf = pikepdf.Pdf.open(input_path)
        page = pdf.pages[page_num]
        mediabox = page.mediabox
        pw = float(mediabox[2]) - float(mediabox[0])
        ph = float(mediabox[3]) - float(mediabox[1])

        # Create overlay PDF with reportlab
        overlay_buf = io.BytesIO()
        c = rl_canvas.Canvas(overlay_buf, pagesize=(pw, ph))
        c.setFont(font_name, font_size)
        r, g, b = [v / 255.0 if v > 1 else v for v in color]
        c.setFillColorRGB(r, g, b)
        # y is from top in frontend, convert to bottom-origin for PDF
        c.drawString(x, ph - y, text)
        c.save()
        overlay_buf.seek(0)

        overlay_pdf = pikepdf.Pdf.open(overlay_buf)
        overlay_page = overlay_pdf.pages[0]

        # Stamp overlay onto target page
        page.add_overlay(overlay_page)

        out = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        pdf.save(out.name)
        pdf.close()
        overlay_pdf.close()
        return out.name

    @staticmethod
    def annotate(input_path: str, page_num: int, overlay_data_url: str) -> str:
        """Stamp a PNG annotation overlay (from Fabric.js) onto a PDF page via reportlab."""
        header, data = overlay_data_url.split(",", 1)
        overlay_bytes = base64.b64decode(data)

        pdf = pikepdf.Pdf.open(input_path)
        page = pdf.pages[page_num]
        mediabox = page.mediabox
        pw = float(mediabox[2]) - float(mediabox[0])
        ph = float(mediabox[3]) - float(mediabox[1])

        # Create overlay PDF with the PNG image
        overlay_buf = io.BytesIO()
        c = rl_canvas.Canvas(overlay_buf, pagesize=(pw, ph))
        img_reader = io.BytesIO(overlay_bytes)
        from reportlab.lib.utils import ImageReader
        img = ImageReader(img_reader)
        c.drawImage(img, 0, 0, width=pw, height=ph, mask="auto")
        c.save()
        overlay_buf.seek(0)

        overlay_pdf = pikepdf.Pdf.open(overlay_buf)
        page.add_overlay(overlay_pdf.pages[0])

        out = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        pdf.save(out.name)
        pdf.close()
        overlay_pdf.close()
        return out.name

    @staticmethod
    def get_page_count(input_path: str) -> int:
        pdf = pikepdf.Pdf.open(input_path)
        count = len(pdf.pages)
        pdf.close()
        return count
