import base64
import io
import tempfile

import pikepdf
from PIL import Image
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
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
    def images_to_pdf(image_paths: list[str]) -> str:
        """One image per page, scaled to fit A4. Returns path to temp PDF."""
        a4_w, a4_h = A4
        out = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        c = rl_canvas.Canvas(out.name, pagesize=A4)
        for path in image_paths:
            img = Image.open(path)
            iw, ih = img.size
            scale = min(a4_w / iw, a4_h / ih)
            draw_w = iw * scale
            draw_h = ih * scale
            x = (a4_w - draw_w) / 2
            y = (a4_h - draw_h) / 2
            reader = ImageReader(path)
            c.drawImage(reader, x, y, width=draw_w, height=draw_h)
            c.showPage()
        c.save()
        return out.name

    @staticmethod
    def apply_annotation_layers(src_pdf_path: str, layers: list[dict]) -> str:
        """Render annotation layers onto a PDF and return path to temp result PDF.

        Each layer dict has:
          type="text": page, text, x, y, font_size, font_name, color ([r,g,b])
          type="image": page, png (data-url of client-rendered Fabric PNG)
        """
        from collections import defaultdict
        by_page: dict[int, list] = defaultdict(list)
        for layer in layers:
            by_page[int(layer["page"])].append(layer)

        pdf = pikepdf.Pdf.open(src_pdf_path)
        for page_num, page_layers in by_page.items():
            if page_num >= len(pdf.pages):
                continue
            page = pdf.pages[page_num]
            mediabox = page.mediabox
            pw = float(mediabox[2]) - float(mediabox[0])
            ph = float(mediabox[3]) - float(mediabox[1])

            overlay_buf = io.BytesIO()
            c = rl_canvas.Canvas(overlay_buf, pagesize=(pw, ph))
            for layer in page_layers:
                if layer.get("type") == "text":
                    font_name = layer.get("font_name", "Helvetica")
                    font_size = float(layer.get("font_size", 12))
                    color = layer.get("color", [0, 0, 0])
                    r, g, b = [v / 255.0 if v > 1 else v for v in color]
                    c.setFont(font_name, font_size)
                    c.setFillColorRGB(r, g, b)
                    c.drawString(float(layer["x"]), ph - float(layer["y"]), layer["text"])
                elif layer.get("type") == "image":
                    png_data_url = layer["png"]
                    _, data = png_data_url.split(",", 1)
                    overlay_bytes = base64.b64decode(data)
                    img = ImageReader(io.BytesIO(overlay_bytes))
                    c.drawImage(img, 0, 0, width=pw, height=ph, mask="auto")
            c.save()
            overlay_buf.seek(0)

            overlay_pdf = pikepdf.Pdf.open(overlay_buf)
            page.add_overlay(overlay_pdf.pages[0])
            overlay_pdf.close()

        out = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        pdf.save(out.name)
        pdf.close()
        return out.name

    @staticmethod
    def get_page_count(input_path: str) -> int:
        pdf = pikepdf.Pdf.open(input_path)
        count = len(pdf.pages)
        pdf.close()
        return count
