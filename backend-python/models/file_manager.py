import os
import shutil
import tempfile
import uuid
from typing import BinaryIO

import config
from models.annotation_store import AnnotationStore
from models.audit_logger import AuditLogger
from models.image_enhancer import ImageEnhancer
from models.image_processor import ImageProcessor
from models.pdf_processor import PdfProcessor
from models.version_store import VersionStore


class FileManager:
    # --- File operations ---

    @staticmethod
    def upload(filename: str, stream: BinaryIO, user: str = "anonymous") -> dict:
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
    def get_file_path(file_id: str, version=None) -> str | None:
        """Return the current (or original) path. version param is ignored."""
        return VersionStore.get_current_path(file_id)

    # --- PDF structural operations (write to current/) ---

    @staticmethod
    def pdf_rotate_page(file_id: str, page_num: int, angle: int, user: str = "anonymous"):
        src = VersionStore.get_current_path(file_id)
        result = PdfProcessor.rotate_page(src, page_num, angle)
        VersionStore.update_current(file_id, result)
        os.unlink(result)
        AuditLogger.log("pdf_rotate_page", file_id, user, {"page": page_num, "angle": angle})

    @staticmethod
    def pdf_delete_page(file_id: str, page_num: int, user: str = "anonymous"):
        src = VersionStore.get_current_path(file_id)
        result = PdfProcessor.delete_page(src, page_num)
        VersionStore.update_current(file_id, result)
        os.unlink(result)
        AuditLogger.log("pdf_delete_page", file_id, user, {"page": page_num})

    @staticmethod
    def pdf_reorder_pages(file_id: str, new_order: list[int], user: str = "anonymous"):
        src = VersionStore.get_current_path(file_id)
        result = PdfProcessor.reorder_pages(src, new_order)
        VersionStore.update_current(file_id, result)
        os.unlink(result)
        AuditLogger.log("pdf_reorder_pages", file_id, user, {"order": new_order})

    @staticmethod
    def pdf_merge(file_ids: list[str], user: str = "anonymous") -> dict:
        paths = []
        for fid in file_ids:
            p = VersionStore.get_current_path(fid)
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
        if enhance_options is None:
            enhance_options = {}
        enhanced_paths = []
        try:
            for fid in file_ids:
                src = VersionStore.get_current_path(fid)
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
                    user: str = "anonymous"):
        import fitz
        if enhance_options is None:
            enhance_options = {}
        src = VersionStore.get_current_path(file_id)
        if not src:
            raise ValueError(f"File not found: {file_id}")
        doc = fitz.open(src)
        tmp_files = []
        try:
            enhanced_paths = []
            for page in doc:
                mat = fitz.Matrix(2, 2)
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
            VersionStore.update_current(file_id, result)
            AuditLogger.log("pdf_enhance", file_id, user, enhance_options)
        finally:
            doc.close()
            for p in tmp_files:
                if os.path.exists(p):
                    os.unlink(p)

    # --- PDF annotation operations (save to AnnotationStore, no PDF modification) ---

    @staticmethod
    def pdf_add_text_overlay(file_id: str, page_num: int, text: str, x: float, y: float,
                             font_size: float = 12, font_name: str = "Helvetica",
                             color: tuple = (0, 0, 0), user: str = "anonymous"):
        data = AnnotationStore.get(file_id, user)
        data.setdefault("text_overlays", []).append({
            "page": page_num, "text": text, "x": x, "y": y,
            "font_size": font_size, "font_name": font_name, "color": list(color),
        })
        AnnotationStore.save(file_id, user, data)
        AuditLogger.log("pdf_text_overlay", file_id, user, {"page": page_num, "text": text})

    @staticmethod
    def pdf_add_annotations(file_id: str, page_num: int, fabric_json: dict,
                            user: str = "anonymous"):
        data = AnnotationStore.get(file_id, user)
        data.setdefault("fabric_pages", {})[str(page_num)] = fabric_json
        AnnotationStore.save(file_id, user, data)
        AuditLogger.log("pdf_annotate", file_id, user, {"page": page_num})

    # --- Image structural operations (write to current/) ---

    @staticmethod
    def image_crop(file_id: str, left: int, top: int, right: int, bottom: int,
                   user: str = "anonymous"):
        src = VersionStore.get_current_path(file_id)
        result = ImageProcessor.crop(src, left, top, right, bottom)
        VersionStore.update_current(file_id, result)
        os.unlink(result)
        AuditLogger.log("image_crop", file_id, user,
                        {"left": left, "top": top, "right": right, "bottom": bottom})

    @staticmethod
    def image_resize(file_id: str, width: int, height: int, user: str = "anonymous"):
        src = VersionStore.get_current_path(file_id)
        result = ImageProcessor.resize(src, width, height)
        VersionStore.update_current(file_id, result)
        os.unlink(result)
        AuditLogger.log("image_resize", file_id, user, {"width": width, "height": height})

    @staticmethod
    def image_rotate(file_id: str, angle: float, user: str = "anonymous"):
        src = VersionStore.get_current_path(file_id)
        result = ImageProcessor.rotate(src, angle)
        VersionStore.update_current(file_id, result)
        os.unlink(result)
        AuditLogger.log("image_rotate", file_id, user, {"angle": angle})

    @staticmethod
    def image_adjust(file_id: str, brightness: float = 1.0, contrast: float = 1.0,
                     saturation: float = 1.0, user: str = "anonymous"):
        src = VersionStore.get_current_path(file_id)
        result = ImageProcessor.adjust(src, brightness, contrast, saturation)
        VersionStore.update_current(file_id, result)
        os.unlink(result)
        AuditLogger.log("image_adjust", file_id, user,
                        {"brightness": brightness, "contrast": contrast, "saturation": saturation})

    @staticmethod
    def image_annotate(file_id: str, overlay_data_url: str, user: str = "anonymous"):
        src = VersionStore.get_current_path(file_id)
        result = ImageProcessor.annotate(src, overlay_data_url)
        VersionStore.update_current(file_id, result)
        os.unlink(result)
        AuditLogger.log("image_annotate", file_id, user)

    # --- Reset ---

    @staticmethod
    def reset_to_original(file_id: str, user: str = "anonymous"):
        """Delete current/ file and all annotation layers, reverting to original."""
        meta = VersionStore.get_metadata(file_id)
        if not meta:
            raise ValueError(f"File not found: {file_id}")
        curr = os.path.join(config.CURRENT_DIR, f"{file_id}.{meta['ext']}")
        if os.path.exists(curr):
            os.remove(curr)
        AnnotationStore.delete_all(file_id)
        AuditLogger.log("reset_to_original", file_id, user)
