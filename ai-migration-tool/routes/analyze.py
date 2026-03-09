from __future__ import annotations

from flask import Blueprint, jsonify, request

from services.cleaner import (
    clean_legacy_dataframe,
    load_legacy_csv,
    write_clean_excel,
    dynamic_cleaning
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
    # load the data
    raw_df = load_legacy_csv(uploaded_path)
    # Claude analysis
    claude_out = run_migration_readiness_analysis(raw_df)
    # Uses claude's response to dynamically clean data and update column names
    clean_df = dynamic_cleaning(raw_df, claude_out)
    # outputs the cleaned data
    excel_path = write_clean_excel(clean_df)

    return jsonify(
        {
            "message": "Analysis complete (stubbed)",
            "excel_output_path": excel_output_path,
            "audit_report": audit_report,
            "cleaned_rows": clean_df.to_dict(orient="records")
        }
    ), 200
