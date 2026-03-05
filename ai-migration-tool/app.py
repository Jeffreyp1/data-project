from __future__ import annotations

import os

from flask import Flask
from flask_cors import CORS

from routes.analyze import analyze_bp
from routes.upload import upload_bp


def create_app() -> Flask:
    """
    App factory for the Flask backend.

    - Enables CORS for the React dev server at http://localhost:3000
    - Registers blueprints for upload + analysis endpoints
    - Ensures required folders exist (uploads/ and outputs/)
    """
    app = Flask(__name__)

    CORS(
        app,
        resources={r"/*": {"origins": "http://localhost:3000"}},
        supports_credentials=False,
    )

    app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "uploads")
    app.config["OUTPUT_FOLDER"] = os.path.join(os.path.dirname(__file__), "outputs")

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["OUTPUT_FOLDER"], exist_ok=True)

    app.register_blueprint(upload_bp, url_prefix="/api")
    app.register_blueprint(analyze_bp, url_prefix="/api")

    return app


app = create_app()

@app.route("/api/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    # Development entrypoint. In production, use a WSGI server (gunicorn, etc.).
    app.run(host="0.0.0.0", port=5001, debug=True)
