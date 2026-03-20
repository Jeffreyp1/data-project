from __future__ import annotations

import os
from typing import Any, Dict
import json
import pandas as pd
from anthropic import Anthropic
from services.cleaner import get_cleaning_toolkit
from services.sap_schemas import SAP_SCHEMAS
import logging

logger = logging.getLogger(__name__)

def _get_anthropic_client() -> Anthropic:

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set in .env")
    return Anthropic(api_key=api_key)

def detect_schema(df: pd.DataFrame) -> str:
    columns = df.columns.tolist()
    sample_rows = df.head(5).to_dict(orient='records')
    sap_types = list(SAP_SCHEMAS.keys())

    prompt = f"""
    You are an SAP S/4HANA data migration assistant.

    You are being given two things:
    1. A list of column names from a legacy ERP CSV export
    2. 3 sample rows of actual data from that CSV

    Using BOTH the column names AND the sample row values together, determine
    which SAP master data schema this CSV most likely belongs to.

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    COLUMN NAMES
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    {json.dumps(columns, indent=2)}

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    SAMPLE ROWS (3 rows)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    {json.dumps(sample_rows, indent=2, default=str)}

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    VALID SAP SCHEMA TYPES
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    {json.dumps(sap_types, indent=2)}

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    INSTRUCTIONS
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Use these guidelines to determine the schema type:
    - customer:  data about companies or people who buy from you
                (look for: customer IDs, revenue, order history, billing address)
    - vendor:    data about suppliers you purchase from
                (look for: vendor IDs, payment terms, invoice info, purchasing data)
    - material:  data about physical products or inventory items
                (look for: product codes, descriptions, units of measure, weights)
    - employee:  data about staff or personnel
                (look for: employee IDs, hire dates, departments, job titles, salaries)

    CRITICAL: Return a single word only — exactly one of the valid schema types listed above.
    No explanation. No punctuation. No extra text. Just the single word.

    Example of correct response: customer
    Example of incorrect response: This looks like customer data because...
    """
    _client = _get_anthropic_client()
    try:
        resp = _client.messages.create(
            model="claude-opus-4-6", max_tokens=10, messages=[{"role": "user", "content": prompt}]
        )
        detected = resp.content[0].text.strip().lower()
        #customer becomes the default if we can't detect it
        if detected not in SAP_SCHEMAS:
            logger.info(f"Claude returned unknown type '{detected}'. Defaulting to customer schema")
            return "customer"
        return detected
    except Exception as e:
        logger.error(f"schema detectionn failed: {e}. Defaulting to customer chema")
        return "customer"


def build_mapping_prompt(df: pd.DataFrame, schema: dict, schema_label: str, required_fields: set) -> str:
    columns = df.columns.tolist()
    sample_rows = df.head(5).to_dict(orient='records')
    toolkit_keys = list(get_cleaning_toolkit().keys())
    required_values = ", ".join(required_fields)
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
        TARGET SAP: {schema_label}
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        {json.dumps(schema, indent=2)}

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
            BLOCKED     — a required field {required_values} is missing entirely

        6. Write a concise audit_report_text covering these points in order:
        - One sentence: how many of the 5 SAMPLE records are migration-ready — explicitly state "based on 5 sample rows" so it is clear this is not the full dataset
        - Bullet list of what was successfully auto-cleaned (e.g. phones normalized, country codes standardized)
        - Bullet list of what needs consultant attention (low confidence mappings, missing fields, format issues)
        Keep each bullet to one line. No long paragraphs. 

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


def run_migration_readiness_analysis(df: pd.DataFrame, schema: dict, schema_label: str, required: set) -> Dict[str, Any]:


    _client = _get_anthropic_client()
    _prompt = build_mapping_prompt(df, schema, schema_label, required)
    fallback = {
        "field_mappings":    [],
        "unmapped_columns":  df.columns.tolist(),
        "readiness": {
            "status":  "BLOCKED",
            "reasons": ["Claude API unavailable — manual review required"]
        },
        "audit_report_text": "Claude API unavailable. All columns flagged for manual review."
    }

    try:
        resp = _client.messages.create(
            model="claude-opus-4-6", max_tokens=2048, messages=[{"role": "user", "content": _prompt}]
        )
        #transform the response into text
        resp_text = resp.content[0].text
        result_text = resp_text.replace("```json", "").replace("```", "").strip()
        start = result_text.find('{')
        end   = result_text.rfind('}') + 1
        result_text = result_text[start:end]
        return json.loads(result_text)
    except json.JSONDecodeError as e:
        logger.error(f"Claude returned invalid JSON: {e}")
        return fallback

    except Exception as e:
        logger.error(f"Error calling Claude API: {e}")
        return fallback


