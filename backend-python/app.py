import os

from flask import Flask, send_from_directory

import config

# Path to the frontend SPA directory (sibling of backend-python)
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")


def create_app(url_prefix: str = ""):
    """Create the DocEditor Flask app.

    Args:
        url_prefix: Mount all API routes under this prefix (e.g. "/doceditor").
                    Can also be set via DOCEDITOR_PREFIX env var.
    """
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_UPLOAD_SIZE

    # Initialize database
    from models.database import init_db
    from models import db_models  # noqa: F401 - ensure models are registered
    init_db(config.DATABASE_URL)

    prefix = url_prefix or config.URL_PREFIX

    from routes.files import files_bp
    from routes.pdf_routes import pdf_bp
    from routes.image_routes import image_bp
    from routes.version_routes import version_bp
    from routes.annotation_routes import annotation_bp

    app.register_blueprint(files_bp, url_prefix=prefix)
    app.register_blueprint(pdf_bp, url_prefix=prefix)
    app.register_blueprint(image_bp, url_prefix=prefix)
    app.register_blueprint(version_bp, url_prefix=prefix)
    app.register_blueprint(annotation_bp, url_prefix=prefix)

    # Serve the SPA frontend
    @app.route("/")
    def serve_index():
        return send_from_directory(FRONTEND_DIR, "index.html")

    @app.route("/<path:path>")
    def serve_frontend(path):
        # Serve frontend files (js/, css/, etc.)
        full_path = os.path.join(FRONTEND_DIR, path)
        if os.path.isfile(full_path):
            return send_from_directory(FRONTEND_DIR, path)
        # Only serve index.html for navigational routes, not missing assets
        if path.endswith((".js", ".css", ".map", ".png", ".jpg", ".ico")):
            return "Not found", 404
        # Fallback to index.html for SPA routing (e.g. old /view/... bookmarks)
        return send_from_directory(FRONTEND_DIR, "index.html")

    # Optional CORS headers for cross-origin frontend hosting
    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    return app


def register_blueprints(app: Flask, url_prefix: str = "/doceditor"):
    """Register DocEditor blueprints into an existing Flask app.

    Usage in another project:
        import sys
        sys.path.insert(0, "path/to/doceditor/backend-python")
        from app import register_blueprints
        register_blueprints(app, url_prefix="/doceditor")
    """
    import sys
    sys.path.insert(0, os.path.dirname(__file__))

    from routes.files import files_bp
    from routes.pdf_routes import pdf_bp
    from routes.image_routes import image_bp
    from routes.version_routes import version_bp
    from routes.annotation_routes import annotation_bp

    app.register_blueprint(files_bp, url_prefix=url_prefix)
    app.register_blueprint(pdf_bp, url_prefix=url_prefix)
    app.register_blueprint(image_bp, url_prefix=url_prefix)
    app.register_blueprint(version_bp, url_prefix=url_prefix)
    app.register_blueprint(annotation_bp, url_prefix=url_prefix)


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
