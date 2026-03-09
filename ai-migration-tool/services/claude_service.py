from __future__ import annotations

import os
from typing import Any, Dict
import json
import pandas as pd
from anthropic import Anthropic
from services.cleaner import get_cleaning_toolkit

SAP_CUSTOMER_SCHEMA = {
    ##identity
    "KUNNR":     "Customer Number (10-digit, zero-padded)",
    "NAME1":     "Customer Name - Primary (required)",
    "NAME2":     "Customer Name - Secondary / DBA name (optional)",

    ##contact
    "TELNR":     "Phone Number (primary)",
    "TELFX":     "Fax Number",
    "SMTP_ADDR": "Email Address",
    ##address of customer 
    "STRAS":     "Street Address",
    "ORT01":     "City",
    "PSTLZ":     "Postal Code / ZIP",
    "REGIO":     "Region / State Code (ISO)",
    "LAND1":     "Country Code (ISO 2-letter, required)",

    ##financials of customer 
    "UMSAV":     "Annual Revenue (numeric, no currency symbol)",
    "WAERS":     "Currency Code (USD, EUR, GBP)",
    "KDGRP":     "Customer Group / Segment",

    ##status of table
    "AUFSD":     "Order Block Flag (blank = active, * = blocked)",
}
def _get_anthropic_client() -> Anthropic:

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set in .env")
    return Anthropic(api_key=api_key)


def build_mapping_prompt(df: pd.DataFrame) -> str:
    """
    Build the prompt for Claude to map legacy fields to SAP target fields.

    Intended behavior:
    - Summarize columns, sample values, and inferred datatypes
    - Ask for proposed SAP S/4HANA target fields + transformation rules
    - Ask for data quality/migration readiness findings
    - Ask for an audit report format (markdown or structured JSON)
    """
    # TODO: craft a strong, deterministic prompt
    columns = df.columns.tolist()
    sample_rows = df.head(5).to_dict()
    toolkit_keys = list(get_cleaning_toolkit().keys())
    prompt = f"""
        You are an SAP S/4HANA data migration assistant.

        You will be given:
        - A list of column names from a legacy ERP CSV export
        - 5 sample rows of actual data from that CSV
        - The target SAP S/4HANA Customer schema (field name → description)
        - A list of available Python cleaning functions

        Your job is to analyze the columns and sample data, then return a JSON object
        mapping each source column to the correct SAP field and cleaning function.

        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        SOURCE COLUMNS
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        {json.dumps(columns, indent=2)}

        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        SAMPLE DATA (5 rows)
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        {json.dumps(sample_rows, indent=2, default=str)}

        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        TARGET SAP S/4HANA CUSTOMER SCHEMA
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        {json.dumps(SAP_CUSTOMER_SCHEMA, indent=2)}

        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        AVAILABLE CLEANING FUNCTIONS
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        {json.dumps(toolkit_keys, indent=2)}

        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        INSTRUCTIONS
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        1. Map each source column to the most appropriate SAP field based on
        the column name AND the actual sample values you can see.

        2. Select the most appropriate cleaning function for each column
        based on what the data actually looks like in the sample rows.

        3. Assign a confidence score (0.0 to 1.0) reflecting how certain
        you are about the mapping. Use these guidelines:
            1.0  — exact or near-exact match (e.g. "email" → SMTP_ADDR)
            0.9  — strong contextual match (e.g. "anual_revnue" → UMSAV)
            0.75 — reasonable inference (e.g. "ref_code" → KUNNR)
            0.5  — ambiguous, needs human review
        Flag anything below 0.80 — a human consultant will review those.

        4. List any columns you cannot confidently map to any SAP field
        in unmapped_columns.

        5. Assess overall migration readiness:
            READY       — all required fields mapped with confidence >= 0.80
            NEEDS_REVIEW — one or more mappings below 0.80 confidence
            BLOCKED     — a required field (KUNNR or NAME1) is missing entirely

        6. Write a short plain-English audit_report_text (3-5 sentences)
        summarizing what you found, what was cleaned, and what needs
        human attention. Write it as if addressing an SAP consultant.

        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        RESPONSE FORMAT
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        Return ONLY valid JSON. No explanation, no markdown, no code fences.
        Use exactly this structure:

        {{
        "field_mappings": [
            {{
            "source":      "original_column_name",
            "target":      "SAP_FIELD_NAME",
            "cleaning_fn": "function_name",
            "confidence":  0.95
            }}
        ],
        "unmapped_columns":  ["col1", "col2"],
        "readiness": {{
            "status":  "NEEDS_REVIEW",
            "reasons": ["anual_revnue mapping below 0.80 confidence"]
        }},
        "audit_report_text": "9 of 10 records are migration-ready..."
        }}
        """
    return prompt.strip()


def run_migration_readiness_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Call Claude to perform field mapping and migration readiness analysis.

    Intended behavior:
    - Create client
    - Build prompt from `df`
    - Send request to a chosen Claude model
    - Parse the response into a structured dict:
      - recommended_field_mappings
      - required_transformations
      - readiness_score / blockers
      - audit_report_text
    """
    _client = _get_anthropic_client()
    _prompt = build_mapping_prompt(df)

    # TODO: call Claude via anthropic SDK and parse response
    try:
        resp = _client.messages.create(
            model="claude-opus-4-6", max_tokens=1024, messages=[{"role": "user", "content": _prompt}]
        )
        #transform the response into text
        resp_text = resp.content[0].text
        result_text = resp_text.replace("```json", "").replace("```", "").strip()
        return json.loads(result_text)
    except Exception as e:
        print("Error sending the prompt: ", e)
        return {}


