from __future__ import annotations

from flask import Blueprint, jsonify, request
import numpy as np
from services.cleaner import (
    load_legacy_csv,
    write_clean_excel,
    dynamic_cleaning
)
from services.claude_service import (
    run_migration_readiness_analysis,
    detect_schema
)
from services.sap_schemas import SAP_SCHEMAS

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

    schema_type = detect_schema(raw_df)
    schema_info = SAP_SCHEMAS[schema_type]
    # send to claude the raw dataframe for analysis (field mapping and readiness analysis)
    claude_out = run_migration_readiness_analysis(raw_df, schema_info['schema'], schema_info['label'],schema_info['required'])
    # parse Claude's response 
    audit_report = {
        'object_type': schema_type,
        'object_type': schema_info['label'],
        'required_fields':   list(schema_info['required']),
        'field_mappings':    claude_out['field_mappings'],
        'unmapped_columns':  claude_out['unmapped_columns'],
        'readiness':         claude_out['readiness'],
        'audit_report_text': claude_out['audit_report_text'],
    }
    # Uses claude's response to dynamically clean data and update column names
    clean_df = dynamic_cleaning(raw_df, claude_out, schema_info['required'])
    # outputs the cleaned data
    excel_path = write_clean_excel(clean_df)

    return jsonify(
        {
            "excel_output_path": excel_path,
            "audit_report": audit_report,
            "raw_columns":       raw_df.columns.tolist(),
            "clean_columns":     clean_df.columns.tolist(),
            "raw_rows":          raw_df.replace({np.nan: None}).to_dict(orient="records"),
            "cleaned_rows":      clean_df.replace({np.nan: None}).to_dict(orient="records"),
        }
    ), 200
