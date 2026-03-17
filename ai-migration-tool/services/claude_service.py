from __future__ import annotations

import os
from typing import Any, Dict
import json
import pandas as pd
from anthropic import Anthropic
from services.cleaner import get_cleaning_toolkit

SAP_CUSTOMER_SCHEMA = {
    "KUNNR":     "Customer Number (10-digit, zero-padded)",
    "NAME1":     "Customer Name - Primary (required)",
    "NAME2":     "Customer Name - Secondary / DBA name (optional)",
    "TELNR":     "Phone Number (primary)",
    "TELFX":     "Fax Number",
    "SMTP_ADDR": "Email Address",
    "STRAS":     "Street Address",
    "ORT01":     "City",
    "PSTLZ":     "Postal Code / ZIP",
    "REGIO":     "Region / State Code (ISO)",
    "LAND1":     "Country Code (ISO 2-letter, required)",
    "UMSAV":     "Annual Revenue (numeric, no currency symbol)",
    "WAERS":     "Currency Code (USD, EUR, GBP)",
    "KDGRP":     "Customer Group / Segment",
    "AUFSD":     "Order Block Flag (blank = active, * = blocked)",
}

SAP_VENDOR_SCHEMA = {
    "LIFNR":     "Vendor Number (10-digit, zero-padded, required)",
    "NAME1":     "Vendor Name - Primary (required)",
    "NAME2":     "Vendor Name - Secondary (optional)",
    "TELNR":     "Phone Number",
    "SMTP_ADDR": "Email Address",
    "STRAS":     "Street Address",
    "ORT01":     "City",
    "PSTLZ":     "Postal Code / ZIP",
    "LAND1":     "Country Code (ISO 2-letter, required)",
    "WAERS":     "Currency Code",
    "ZTERM":     "Payment Terms (e.g. NET30, NET60)",
    "SPERM":     "Purchasing Block Flag (blank = active, X = blocked)",
}

SAP_MATERIAL_SCHEMA = {
    "MATNR":     "Material Number (18-char max, required)",
    "MAKTX":     "Material Description (required)",
    "MATKL":     "Material Group / Category Code",
    "MEINS":     "Base Unit of Measure (EA, KG, LB, PC)",
    "MTART":     "Material Type (FERT=Finished, ROH=Raw, HALB=Semi-finished)",
    "MBRSH":     "Industry Sector (M=Mechanical, E=Electrical, etc.)",
    "NTGEW":     "Net Weight (numeric)",
    "BRGEW":     "Gross Weight (numeric)",
    "GEWEI":     "Weight Unit (KG, LB)",
    "VOLUM":     "Volume (numeric)",
    "VOLEH":     "Volume Unit (L, GAL, CM3)",
}

SAP_EMPLOYEE_SCHEMA = {
    "PERNR":     "Personnel Number (8-digit, zero-padded, required)",
    "VORNA":     "First Name (required)",
    "NACHN":     "Last Name (required)",
    "GBDAT":     "Date of Birth (YYYY-MM-DD)",
    "AEDTM":     "Hire Date (YYYY-MM-DD)",
    "PLANS":     "Position Code",
    "ORGEH":     "Organizational Unit",
    "STELL":     "Job Code",
    "WERKS":     "Plant / Work Location Code",
    "MOLGA":     "Country Grouping (01=USA, 02=Canada)",
    "ANSVH":     "Employment Status (1=Active, 0=Inactive)",
}


SAP_SCHEMAS = {
    "customer": {
        "schema":   SAP_CUSTOMER_SCHEMA,
        "required": {"KUNNR", "NAME1"},
        "label":    "SAP Customer Master (KNA1)"
    },
    "vendor": {
        "schema":   SAP_VENDOR_SCHEMA,
        "required": {"LIFNR", "NAME1"},
        "label":    "SAP Vendor Master (LFA1)"
    },
    "material": {
        "schema":   SAP_MATERIAL_SCHEMA,
        "required": {"MATNR", "MAKTX"},
        "label":    "SAP Material Master (MARA)"
    },
    "employee": {
        "schema":   SAP_EMPLOYEE_SCHEMA,
        "required": {"PERNR", "VORNA", "NACHN"},
        "label":    "SAP Employee Master (PA0001)"
    },
}
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
            print(f"Claude returned unknown type '{detected}'. Defaulting to customer schema")
            return "customer"
        return detected
    except Exception as e:
        print(f"schema detectionn failed: {e}. Defaulting to customer chema")
        return "customer"


def build_mapping_prompt(df: pd.DataFrame, schema: dict, schema_label: str, required_fields: set) -> str:
    """
    Build the prompt for Claude to map legacy fields to SAP target fields.

    Intended behavior:
    - Summarize columns, sample values, and inferred datatypes
    - Ask for proposed SAP S/4HANA target fields + transformation rules
    - Ask for data quality/migration readiness findings
    - Ask for an audit report format (markdown or structured JSON)
    """
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


def run_migration_readiness_analysis(df: pd.DataFrame, schema: dict, schema_label: str, required: set) -> Dict[str, Any]:
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
            model="claude-opus-4-6", max_tokens=1024, messages=[{"role": "user", "content": _prompt}]
        )
        #transform the response into text
        resp_text = resp.content[0].text
        result_text = resp_text.replace("```json", "").replace("```", "").strip()
        return json.loads(result_text)
    except json.JSONDecodeError as e:
        print(f"Claude returned invalid JSON: {e}")
        return fallback

    except Exception as e:
        print(f"Error calling Claude API: {e}")
        return fallback


