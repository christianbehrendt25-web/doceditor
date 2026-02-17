from flask import Flask
import config


def create_app(url_prefix: str = ""):
    """Create the DocEditor Flask app.

    Args:
        url_prefix: Mount all routes under this prefix (e.g. "/doceditor").
                    Can also be set via DOCEDITOR_PREFIX env var.
    """
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_UPLOAD_SIZE

    prefix = url_prefix or config.URL_PREFIX

    from routes.files import files_bp
    from routes.pdf_routes import pdf_bp
    from routes.image_routes import image_bp
    from routes.version_routes import version_bp

    app.register_blueprint(files_bp, url_prefix=prefix)
    app.register_blueprint(pdf_bp, url_prefix=prefix)
    app.register_blueprint(image_bp, url_prefix=prefix)
    app.register_blueprint(version_bp, url_prefix=prefix)

    return app


def register_blueprints(app: Flask, url_prefix: str = "/doceditor"):
    """Register DocEditor blueprints into an existing Flask app.

    Usage in another project:
        import sys
        sys.path.insert(0, "path/to/doceditor")
        from app import register_blueprints
        register_blueprints(app, url_prefix="/doceditor")
    """
    import os
    import sys
    sys.path.insert(0, os.path.dirname(__file__))

    from routes.files import files_bp
    from routes.pdf_routes import pdf_bp
    from routes.image_routes import image_bp
    from routes.version_routes import version_bp

    app.register_blueprint(files_bp, url_prefix=url_prefix)
    app.register_blueprint(pdf_bp, url_prefix=url_prefix)
    app.register_blueprint(image_bp, url_prefix=url_prefix)
    app.register_blueprint(version_bp, url_prefix=url_prefix)


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
