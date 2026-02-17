import base64
import io
import tempfile

from PIL import Image, ImageEnhance


class ImageProcessor:
    @staticmethod
    def crop(input_path: str, left: int, top: int, right: int, bottom: int) -> str:
        img = Image.open(input_path)
        cropped = img.crop((left, top, right, bottom))
        out = tempfile.NamedTemporaryFile(suffix=_suffix(input_path), delete=False)
        cropped.save(out.name)
        return out.name

    @staticmethod
    def resize(input_path: str, width: int, height: int) -> str:
        img = Image.open(input_path)
        resized = img.resize((width, height), Image.LANCZOS)
        out = tempfile.NamedTemporaryFile(suffix=_suffix(input_path), delete=False)
        resized.save(out.name)
        return out.name

    @staticmethod
    def rotate(input_path: str, angle: float) -> str:
        img = Image.open(input_path)
        rotated = img.rotate(-angle, expand=True)  # negative because PIL rotates counter-clockwise
        out = tempfile.NamedTemporaryFile(suffix=_suffix(input_path), delete=False)
        rotated.save(out.name)
        return out.name

    @staticmethod
    def adjust(input_path: str, brightness: float = 1.0, contrast: float = 1.0, saturation: float = 1.0) -> str:
        img = Image.open(input_path)
        if brightness != 1.0:
            img = ImageEnhance.Brightness(img).enhance(brightness)
        if contrast != 1.0:
            img = ImageEnhance.Contrast(img).enhance(contrast)
        if saturation != 1.0:
            img = ImageEnhance.Color(img).enhance(saturation)
        out = tempfile.NamedTemporaryFile(suffix=_suffix(input_path), delete=False)
        img.save(out.name)
        return out.name

    @staticmethod
    def annotate(input_path: str, overlay_data_url: str) -> str:
        """Composite a PNG overlay (from Fabric.js export as data URL) onto the image."""
        # Parse data URL
        header, data = overlay_data_url.split(",", 1)
        overlay_bytes = base64.b64decode(data)
        overlay = Image.open(io.BytesIO(overlay_bytes)).convert("RGBA")

        base = Image.open(input_path).convert("RGBA")
        # Resize overlay to match base if needed
        if overlay.size != base.size:
            overlay = overlay.resize(base.size, Image.LANCZOS)
        composite = Image.alpha_composite(base, overlay)

        out = tempfile.NamedTemporaryFile(suffix=_suffix(input_path), delete=False)
        # Save as RGB for JPEG, RGBA for PNG
        suffix = _suffix(input_path).lower()
        if suffix in (".jpg", ".jpeg"):
            composite = composite.convert("RGB")
        composite.save(out.name)
        return out.name


def _suffix(path: str) -> str:
    return "." + path.rsplit(".", 1)[-1]
