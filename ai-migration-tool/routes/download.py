from __future__ import annotations

import os
import uuid
from typing import Any

from flask import Blueprint, current_app, jsonify, request, send_file

import pandas as pd

download_bp = Blueprint("download", __name__)

@download_bp.route("/download", methods=["GET"])
def download():
    filename = request.args.get("filename")

    if not filename:
        return jsonify({"error": "Missing filename"}), 400

    file_path = os.path.abspath(filename)


    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    return send_file(file_path, as_attachment=True)
