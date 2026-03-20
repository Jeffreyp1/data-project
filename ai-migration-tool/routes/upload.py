from __future__ import annotations

import os
import uuid
from typing import Any

from flask import Blueprint, current_app, jsonify, request

import pandas as pd
import logging

logger = logging.getLogger(__name__)
upload_bp = Blueprint("upload", __name__)


def _allowed_file(filename: str) -> bool:
    if not filename:
        return False
    
    return filename.endswith(".csv")


def _save_upload_to_disk(file_storage: Any) -> str:
    upload_dir = os.path.abspath(current_app.config["UPLOAD_FOLDER"])
    unique_name = f"{uuid.uuid4().hex}.csv"
    path = os.path.abspath(os.path.join(upload_dir, unique_name))

    data = file_storage.read()
    with open(path, "wb") as f:
        f.write(data)

    if not os.path.exists(path):
        raise RuntimeError(f"Upload save failed: {path} not found after write")
    return path


@upload_bp.route("/upload", methods=["POST"])
def upload_csv():
    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files["file"]
    if file.filename is None or file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not _allowed_file(file.filename):
        return jsonify({"error": "Unsupported file type"}), 400

    try:
        saved_path = _save_upload_to_disk(file)
    except (OSError, RuntimeError) as e:
        return jsonify({"error": f"Failed to save upload: {e}"}), 500

    return jsonify({"message": "Upload received", "uploaded_path": saved_path}), 200
