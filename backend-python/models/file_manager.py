import os
import shutil
import tempfile
import uuid
from typing import BinaryIO

import config
from models.audit_logger import AuditLogger
from models.image_enhancer import ImageEnhancer
from models.image_processor import ImageProcessor
from models.pdf_processor import PdfProcessor
from models.version_store import VersionStore


class FileManager:
    # --- File operations ---

    @staticmethod
    def upload(filename: str, stream: BinaryIO, user: str = "anonymous") -> dict:
        """Upload a file from a filename and binary stream (framework-agnostic).

        Args:
            filename: Original filename (e.g. "document.pdf")
            stream: Binary stream with file contents
            user: Username for audit log
        """
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in config.ALL_ALLOWED:
            raise ValueError(f"File type .{ext} not allowed")

        file_type = "pdf" if ext == "pdf" else "image"
        file_id = uuid.uuid4().hex[:12]
        dest = os.path.join(config.ORIGINALS_DIR, f"{file_id}.{ext}")
        with open(dest, "wb") as f:
            shutil.copyfileobj(stream, f)

        meta = VersionStore.create_metadata(file_id, filename, file_type, ext)
        AuditLogger.log("upload", file_id, user, {"original_name": filename})
        return meta

    @staticmethod
    def list_files() -> list[dict]:
        return VersionStore.list_files()

    @staticmethod
    def get_file_info(file_id: str) -> dict | None:
        return VersionStore.get_metadata(file_id)

    @staticmethod
    def delete_file(file_id: str, user: str = "anonymous"):
        VersionStore.delete_file(file_id)
        AuditLogger.log("delete", file_id, user)

    @staticmethod
    def get_file_path(file_id: str, version: int | None = None) -> str | None:
        if version is not None:
            return VersionStore.get_version_path(file_id, version)
        return VersionStore.get_latest_version_path(file_id)

    # --- PDF operations ---

    @staticmethod
    def pdf_rotate_page(file_id: str, page_num: int, angle: int, user: str = "anonymous") -> int:
        src = VersionStore.get_latest_version_path(file_id)
        result = PdfProcessor.rotate_page(src, page_num, angle)
        v = VersionStore.create_new_version(file_id, result, "pdf_rotate_page", {"page": page_num, "angle": angle})
        os.unlink(result)
        AuditLogger.log("pdf_rotate_page", file_id, user, {"page": page_num, "angle": angle, "version": v})
        return v

    @staticmethod
    def pdf_delete_page(file_id: str, page_num: int, user: str = "anonymous") -> int:
        src = VersionStore.get_latest_version_path(file_id)
        result = PdfProcessor.delete_page(src, page_num)
        v = VersionStore.create_new_version(file_id, result, "pdf_delete_page", {"page": page_num})
        os.unlink(result)
        AuditLogger.log("pdf_delete_page", file_id, user, {"page": page_num, "version": v})
        return v

    @staticmethod
    def pdf_reorder_pages(file_id: str, new_order: list[int], user: str = "anonymous") -> int:
        src = VersionStore.get_latest_version_path(file_id)
        result = PdfProcessor.reorder_pages(src, new_order)
        v = VersionStore.create_new_version(file_id, result, "pdf_reorder_pages", {"order": new_order})
        os.unlink(result)
        AuditLogger.log("pdf_reorder_pages", file_id, user, {"order": new_order, "version": v})
        return v

    @staticmethod
    def pdf_merge(file_ids: list[str], user: str = "anonymous") -> dict:
        paths = []
        for fid in file_ids:
            p = VersionStore.get_latest_version_path(fid)
            if not p:
                raise ValueError(f"File not found: {fid}")
            paths.append(p)
        result = PdfProcessor.merge(paths)
        new_id = uuid.uuid4().hex[:12]
        dest = os.path.join(config.ORIGINALS_DIR, f"{new_id}.pdf")
        shutil.move(result, dest)
        meta = VersionStore.create_metadata(new_id, "merged.pdf", "pdf", "pdf")
        AuditLogger.log("pdf_merge", new_id, user, {"source_files": file_ids})
        return meta

    @staticmethod
    def images_to_pdf(file_ids: list[str], enhance_options: dict | None = None,
                      user: str = "anonymous") -> dict:
        """Convert image files to a single PDF with optional enhancement."""
        if enhance_options is None:
            enhance_options = {}
        enhanced_paths = []
        try:
            for fid in file_ids:
                src = VersionStore.get_latest_version_path(fid)
                if not src:
                    raise ValueError(f"File not found: {fid}")
                enhanced = ImageEnhancer.enhance(
                    src,
                    deskew=enhance_options.get("deskew", True),
                    sharpen=enhance_options.get("sharpen", True),
                    contrast=enhance_options.get("contrast", True),
                    threshold=enhance_options.get("threshold", True),
                )
                enhanced_paths.append(enhanced)

            result = PdfProcessor.images_to_pdf(enhanced_paths)
            new_id = uuid.uuid4().hex[:12]
            dest = os.path.join(config.ORIGINALS_DIR, f"{new_id}.pdf")
            shutil.move(result, dest)
            meta = VersionStore.create_metadata(new_id, "photo-to-pdf.pdf", "pdf", "pdf")
            AuditLogger.log("images_to_pdf", new_id, user, {"source_files": file_ids})
            return meta
        finally:
            for p in enhanced_paths:
                if os.path.exists(p):
                    os.unlink(p)

    @staticmethod
    def pdf_enhance(file_id: str, enhance_options: dict | None = None,
                    user: str = "anonymous") -> int:
        """Render each PDF page as image, apply enhancement, rebuild as new version."""
        import fitz
        if enhance_options is None:
            enhance_options = {}
        src = VersionStore.get_latest_version_path(file_id)
        if not src:
            raise ValueError(f"File not found: {file_id}")
        doc = fitz.open(src)
        tmp_files = []
        try:
            enhanced_paths = []
            for page in doc:
                mat = fitz.Matrix(2, 2)  # ~150 dpi
                pix = page.get_pixmap(matrix=mat)
                raw = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                raw.close()
                tmp_files.append(raw.name)
                pix.save(raw.name)
                enhanced = ImageEnhancer.enhance(
                    raw.name,
                    deskew=enhance_options.get("deskew", True),
                    sharpen=enhance_options.get("sharpen", True),
                    contrast=enhance_options.get("contrast", True),
                    threshold=enhance_options.get("threshold", False),
                )
                tmp_files.append(enhanced)
                enhanced_paths.append(enhanced)
            result = PdfProcessor.images_to_pdf(enhanced_paths)
            tmp_files.append(result)
            v = VersionStore.create_new_version(file_id, result, "pdf_enhance", enhance_options)
            AuditLogger.log("pdf_enhance", file_id, user, {**enhance_options, "version": v})
            return v
        finally:
            doc.close()
            for p in tmp_files:
                if os.path.exists(p):
                    os.unlink(p)

    @staticmethod
    def pdf_add_text_overlay(file_id: str, page_num: int, text: str, x: float, y: float,
                             font_size: float = 12, font_name: str = "Helvetica",
                             color: tuple = (0, 0, 0), user: str = "anonymous") -> int:
        src = VersionStore.get_latest_version_path(file_id)
        result = PdfProcessor.text_overlay(src, page_num, text, x, y, font_size, font_name, color)
        v = VersionStore.create_new_version(file_id, result, "pdf_text_overlay",
                                            {"page": page_num, "text": text, "x": x, "y": y})
        os.unlink(result)
        AuditLogger.log("pdf_text_overlay", file_id, user, {"page": page_num, "version": v})
        return v

    @staticmethod
    def pdf_add_annotations(file_id: str, page_num: int, overlay_data_url: str,
                            user: str = "anonymous") -> int:
        src = VersionStore.get_latest_version_path(file_id)
        result = PdfProcessor.annotate(src, page_num, overlay_data_url)
        v = VersionStore.create_new_version(file_id, result, "pdf_annotate", {"page": page_num})
        os.unlink(result)
        AuditLogger.log("pdf_annotate", file_id, user, {"page": page_num, "version": v})
        return v

    # --- Image operations ---

    @staticmethod
    def image_crop(file_id: str, left: int, top: int, right: int, bottom: int,
                   user: str = "anonymous") -> int:
        src = VersionStore.get_latest_version_path(file_id)
        result = ImageProcessor.crop(src, left, top, right, bottom)
        v = VersionStore.create_new_version(file_id, result, "image_crop",
                                            {"left": left, "top": top, "right": right, "bottom": bottom})
        os.unlink(result)
        AuditLogger.log("image_crop", file_id, user, {"version": v})
        return v

    @staticmethod
    def image_resize(file_id: str, width: int, height: int, user: str = "anonymous") -> int:
        src = VersionStore.get_latest_version_path(file_id)
        result = ImageProcessor.resize(src, width, height)
        v = VersionStore.create_new_version(file_id, result, "image_resize", {"width": width, "height": height})
        os.unlink(result)
        AuditLogger.log("image_resize", file_id, user, {"width": width, "height": height, "version": v})
        return v

    @staticmethod
    def image_rotate(file_id: str, angle: float, user: str = "anonymous") -> int:
        src = VersionStore.get_latest_version_path(file_id)
        result = ImageProcessor.rotate(src, angle)
        v = VersionStore.create_new_version(file_id, result, "image_rotate", {"angle": angle})
        os.unlink(result)
        AuditLogger.log("image_rotate", file_id, user, {"angle": angle, "version": v})
        return v

    @staticmethod
    def image_adjust(file_id: str, brightness: float = 1.0, contrast: float = 1.0,
                     saturation: float = 1.0, user: str = "anonymous") -> int:
        src = VersionStore.get_latest_version_path(file_id)
        result = ImageProcessor.adjust(src, brightness, contrast, saturation)
        v = VersionStore.create_new_version(file_id, result, "image_adjust",
                                            {"brightness": brightness, "contrast": contrast, "saturation": saturation})
        os.unlink(result)
        AuditLogger.log("image_adjust", file_id, user, {"version": v})
        return v

    @staticmethod
    def image_annotate(file_id: str, overlay_data_url: str, user: str = "anonymous") -> int:
        src = VersionStore.get_latest_version_path(file_id)
        result = ImageProcessor.annotate(src, overlay_data_url)
        v = VersionStore.create_new_version(file_id, result, "image_annotate", {})
        os.unlink(result)
        AuditLogger.log("image_annotate", file_id, user, {"version": v})
        return v

    # --- Version operations ---

    @staticmethod
    def revert(file_id: str, version: int, user: str = "anonymous") -> int:
        path = VersionStore.get_version_path(file_id, version)
        if not path:
            raise ValueError(f"Version {version} not found for {file_id}")
        v = VersionStore.create_new_version(file_id, path, "revert", {"reverted_to": version})
        AuditLogger.log("revert", file_id, user, {"reverted_to": version, "new_version": v})
        return v
