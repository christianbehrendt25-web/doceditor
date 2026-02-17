import os

from flask import Blueprint, jsonify, request, send_file

from models.file_manager import FileManager
from models.pdf_processor import PdfProcessor

pdf_bp = Blueprint("pdf", __name__)


@pdf_bp.route("/api/pdf/<file_id>/serve")
def serve_pdf(file_id):
    version = request.args.get("version", None, type=int)
    path = FileManager.get_file_path(file_id, version)
    if not path or not os.path.exists(path):
        return jsonify({"error": "Not found"}), 404
    return send_file(path, mimetype="application/pdf")


@pdf_bp.route("/api/pdf/<file_id>/page-count")
def page_count(file_id):
    path = FileManager.get_file_path(file_id)
    if not path:
        return jsonify({"error": "Not found"}), 404
    count = PdfProcessor.get_page_count(path)
    return jsonify({"page_count": count})


@pdf_bp.route("/api/pdf/<file_id>/rotate-page", methods=["POST"])
def rotate_page(file_id):
    data = request.get_json()
    user = data.get("user", "anonymous")
    try:
        v = FileManager.pdf_rotate_page(file_id, data["page"], data.get("angle", 90), user)
        return jsonify({"version": v})
    except (KeyError, ValueError, IndexError) as e:
        return jsonify({"error": str(e)}), 400


@pdf_bp.route("/api/pdf/<file_id>/delete-page", methods=["POST"])
def delete_page(file_id):
    data = request.get_json()
    user = data.get("user", "anonymous")
    try:
        v = FileManager.pdf_delete_page(file_id, data["page"], user)
        return jsonify({"version": v})
    except (KeyError, ValueError, IndexError) as e:
        return jsonify({"error": str(e)}), 400


@pdf_bp.route("/api/pdf/<file_id>/reorder-pages", methods=["POST"])
def reorder_pages(file_id):
    data = request.get_json()
    user = data.get("user", "anonymous")
    try:
        v = FileManager.pdf_reorder_pages(file_id, data["order"], user)
        return jsonify({"version": v})
    except (KeyError, ValueError, IndexError) as e:
        return jsonify({"error": str(e)}), 400


@pdf_bp.route("/api/pdf/merge", methods=["POST"])
def merge_pdfs():
    data = request.get_json()
    user = data.get("user", "anonymous")
    try:
        meta = FileManager.pdf_merge(data["file_ids"], user)
        return jsonify(meta), 201
    except (KeyError, ValueError) as e:
        return jsonify({"error": str(e)}), 400


@pdf_bp.route("/api/pdf/<file_id>/text-overlay", methods=["POST"])
def text_overlay(file_id):
    data = request.get_json()
    user = data.get("user", "anonymous")
    try:
        v = FileManager.pdf_add_text_overlay(
            file_id, data["page"], data["text"], data["x"], data["y"],
            font_size=data.get("font_size", 12),
            font_name=data.get("font_name", "Helvetica"),
            color=tuple(data.get("color", [0, 0, 0])),
            user=user,
        )
        return jsonify({"version": v})
    except (KeyError, ValueError) as e:
        return jsonify({"error": str(e)}), 400


@pdf_bp.route("/api/pdf/<file_id>/annotate", methods=["POST"])
def annotate_pdf(file_id):
    data = request.get_json()
    user = data.get("user", "anonymous")
    try:
        v = FileManager.pdf_add_annotations(file_id, data["page"], data["overlay"], user)
        return jsonify({"version": v})
    except (KeyError, ValueError) as e:
        return jsonify({"error": str(e)}), 400
