from __future__ import annotations

import os
import uuid
from typing import Any

from flask import Blueprint, current_app, jsonify, request


upload_bp = Blueprint("upload", __name__)


def _allowed_file(filename: str) -> bool:
    """
    Return True if the filename is an allowed upload type.

    Intended behavior:
    - Accept only CSV uploads
    - Guard against missing extensions
    """
    # TODO: implement extension validation (csv only)
    return True


def _save_upload_to_disk(file_storage: Any) -> str:
    """
    Persist an uploaded CSV to the `uploads/` directory.

    Intended behavior:
    - Generate a unique safe filename
    - Save to app.config["UPLOAD_FOLDER"]
    - Return absolute path to the saved file
    """
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    unique_name = f"{uuid.uuid4().hex}.csv"
    path = os.path.join(upload_dir, unique_name)

    # TODO: actually save the file to `path`
    return path


@upload_bp.route("/upload", methods=["POST"])
def upload_csv():
    """
    Handle CSV upload from the frontend.

    Intended behavior:
    - Validate multipart form-data (expects `file`)
    - Validate file type
    - Save to `uploads/`
    - Return a file_id or server path token for later analysis
    """
    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files["file"]
    if file.filename is None or file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not _allowed_file(file.filename):
        return jsonify({"error": "Unsupported file type"}), 400

    saved_path = _save_upload_to_disk(file)

    # TODO: return a stable identifier (not raw path) to reference the upload later
    return jsonify({"message": "Upload received", "uploaded_path": saved_path}), 200
