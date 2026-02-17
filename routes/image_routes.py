import os

from flask import Blueprint, jsonify, request, send_file

from models.file_manager import FileManager

image_bp = Blueprint("image", __name__)


@image_bp.route("/api/image/<file_id>/serve")
def serve_image(file_id):
    version = request.args.get("version", None, type=int)
    path = FileManager.get_file_path(file_id, version)
    if not path or not os.path.exists(path):
        return jsonify({"error": "Not found"}), 404
    return send_file(path)


@image_bp.route("/api/image/<file_id>/crop", methods=["POST"])
def crop_image(file_id):
    data = request.get_json()
    user = data.get("user", "anonymous")
    try:
        v = FileManager.image_crop(file_id, data["left"], data["top"], data["right"], data["bottom"], user)
        return jsonify({"version": v})
    except (KeyError, ValueError) as e:
        return jsonify({"error": str(e)}), 400


@image_bp.route("/api/image/<file_id>/resize", methods=["POST"])
def resize_image(file_id):
    data = request.get_json()
    user = data.get("user", "anonymous")
    try:
        v = FileManager.image_resize(file_id, data["width"], data["height"], user)
        return jsonify({"version": v})
    except (KeyError, ValueError) as e:
        return jsonify({"error": str(e)}), 400


@image_bp.route("/api/image/<file_id>/rotate", methods=["POST"])
def rotate_image(file_id):
    data = request.get_json()
    user = data.get("user", "anonymous")
    try:
        v = FileManager.image_rotate(file_id, data.get("angle", 90), user)
        return jsonify({"version": v})
    except (KeyError, ValueError) as e:
        return jsonify({"error": str(e)}), 400


@image_bp.route("/api/image/<file_id>/adjust", methods=["POST"])
def adjust_image(file_id):
    data = request.get_json()
    user = data.get("user", "anonymous")
    try:
        v = FileManager.image_adjust(
            file_id,
            brightness=data.get("brightness", 1.0),
            contrast=data.get("contrast", 1.0),
            saturation=data.get("saturation", 1.0),
            user=user,
        )
        return jsonify({"version": v})
    except (KeyError, ValueError) as e:
        return jsonify({"error": str(e)}), 400


@image_bp.route("/api/image/<file_id>/annotate", methods=["POST"])
def annotate_image(file_id):
    data = request.get_json()
    user = data.get("user", "anonymous")
    try:
        v = FileManager.image_annotate(file_id, data["overlay"], user)
        return jsonify({"version": v})
    except (KeyError, ValueError) as e:
        return jsonify({"error": str(e)}), 400
