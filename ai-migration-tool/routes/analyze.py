from __future__ import annotations

from flask import Blueprint, jsonify, request

from services.cleaner import (
    clean_legacy_dataframe,
    load_legacy_csv,
    write_clean_excel,
)
from services.claude_service import run_migration_readiness_analysis


analyze_bp = Blueprint("analyze", __name__)


@analyze_bp.route("/analyze", methods=["POST"])
def analyze():
    """
    Run the end-to-end analysis pipeline for a previously uploaded CSV.

    Intended behavior:
    - Receive an identifier for the uploaded CSV (e.g., file_id)
    - Load the raw CSV into pandas
    - Clean/transform with the cleaner service
    - Call Claude to do field mapping + migration readiness analysis
    - Write a clean Excel output to `outputs/`
    - Return metadata: excel filename/path token + audit report content
    """
    payload = request.get_json(silent=True) or {}
    uploaded_path = payload.get("uploaded_path")

    if not uploaded_path:
        return jsonify({"error": "Missing uploaded_path"}), 400

    # 1) Load
    raw_df = load_legacy_csv(uploaded_path)
    if raw_df.empty or len(raw_df.columns) == 0:
        return jsonify({"error": "File not found or file could not be read"}), 404

    # 2) Clean / transform
    try:
        clean_df = clean_legacy_dataframe(raw_df)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    # 3) AI analysis (field mapping + readiness)
    audit_report = run_migration_readiness_analysis(clean_df)

    # 4) Write clean Excel output
    excel_output_path = write_clean_excel(clean_df)

    return jsonify(
        {
            "message": "Analysis complete (stubbed)",
            "excel_output_path": excel_output_path,
            "audit_report": audit_report,
        }
    ), 200
