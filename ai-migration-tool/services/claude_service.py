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
agent_tools = [
    {
        "name": "detect_SAP_schema",
        "description": """Ensure to call this tool first before any other tool. 
        You will be given column names and call determine whether the data belongs to customer, vendor, material, material, or employee SAP Master Data
        CRITICAL: Return a single word only — exactly one of the valid schema types listed above.
        No explanation. No punctuation. No extra text. Just the single word.
        """,
        "input_schema":{
            "type": "object",
            "properties": {
                "columns": {
                    "type": "array",
                    "items":{"type": "string"},
                    "description": "column names retrieved that must be mapped to SAP fields"
                },
                "sample_rows":{
                        "type": "array",
                        "description": "example data values used to determine cleaning function. Rows are list of dictionary"
                }
            },
            "required": ["columns", "sample_rows"]
        },

    },
    {
        "name": "map_columns_to_sap_fields",
        "description": """
            DO NOT use this tool BEFORE detect_sap_schema. Map each source column to the correct 
            SAP field name, assign an appropriate cleaning function to standardize data stored in sample_rows.
            Include a confidence score between (0.0-1.0) for each mapping. Mapping below 0.80 must be flagged
            for review.

        """,
        "input_schema": {
            "type": "object",
            "properties": {
                "columns": {
                    "type": "array",
                    "items":{"type": "string"},
                    "description": "column names that were retrieved from SAP Fields"
                },
                "sample_rows":{
                    "type": "array",
                    "description": "example data values used to determine cleaning function. Rows are list of dictionary"
                },
                "schema_type":{
                    "type": "string",
                    "description": "Schema returned by detect_SAP_schema"
                }
            },
            "required": ["columns", "sample_rows", "schema_type"]
        }
    },
    {"name": "generate_audit_summary",
        "description": """
            Call this last once you have called detect_SAP_schema, map_columns_to_sap_fields, and validate_mapping_completeness.
            
            Write a concise audit_report_text covering these points in order:
            - One sentence: how many of the 5 SAMPLE records are migration-ready — explicitly state "based on 5 sample rows" so it is clear this is not the full dataset
            - Bullet list of what was successfully auto-cleaned (e.g. phones normalized, country codes standardized)
            - Bullet list of what needs consultant attention (low confidence mappings, missing fields, format issues)
            Keep each bullet to one line. No long paragraphs.

            Set readiness.status using these rules:
            - READY: all required fields mapped with confidence >= 0.80
            - NEEDS_REVIEW: one or more mappings below 0.80 confidence
            - BLOCKED: a required field is missing entirely
            Set readiness.reasons to a list of strings explaining why (empty list if READY).
        """,
        "input_schema": {
            "type": "object",
            "properties": {
                "field_mappings": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties" : {
                            "source":      {"type": "string", "description": "original column name from the CSV"},
                            "target": {"type": "string", "description": "the SAP column that best matches source"},
                            "cleaning_fn": {"type": "string", "description": "cleaning function to apply"},
                            "confidence":  {"type": "number", "description": "confidence score between 0.0 and 1.0"}
                        }
                    }
                },
                "unmapped_columns":{
                    "type": "array"
                },
                "schema_type":{
                    "type": "string"
                },
                "readiness": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["READY", "NEEDS_REVIEW", "BLOCKED"]
                        },
                        "reasons": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["status", "reasons"]
                }

            },
            "required": ["field_mappings", "schema_type", "readiness"]
        }
    }
   
    

]

def execute_tool(df: pd.DataFrame, tool_name: str, tool_input: dict) -> dict:
    columns = df.columns.tolist()
    sample_rows = df.head(5).to_dict(orient="records")
    if tool_name == 'detect_SAP_schema':
        return{
            "success": True,
            "columns": columns,
            "sample_rows": sample_rows
        }
    elif tool_name == "map_columns_to_sap_fields":
        return{
            "success": True,
            "columns": columns,
            "sample_rows": sample_rows,
            "schema_type": SAP_SCHEMAS[tool_input["schema_type"]]
        }
    elif tool_name == "generate_audit_summary":
        return {
            "success": True,
            "field_mappings": tool_input["field_mappings"],
            "unmapped_columns": tool_input.get("unmapped_columns", []),
            "validation_result": tool_input.get("validation_result", {}),
            "schema_type": tool_input["schema_type"],
            "readiness": tool_input["readiness"]
        }
    
    return {"success": False, "error": f"Unknown tool: {tool_name}"}

def generate_function(needs_function_generation: list, df: pd.DataFrame) -> list:
    client = _get_anthropic_client()
    toolkit_keys = list(get_cleaning_toolkit().keys())

    # attach sample values to each item so Claude sees the actual input format
    for item in needs_function_generation:
        col = item["column"]
        if col in df.columns:
            item["sample_values"] = df[col].head(5).tolist()

    prompt = f"""
        You are an SAP data migration assistant. Generate a Python cleaning function
        for each column listed below.

        REQUIREMENTS:
        - Each function must accept a pandas Series and return a cleaned pandas Series
        - Apply the transformation element-wise using .apply() or vectorized pandas operations
        - Handle None, NaN, and empty string gracefully — return the value unchanged if it cannot be cleaned
        - CRITICAL: Do NOT include any import statements. The following are already available: pd, re, unicodedata
        - Use pd, re, unicodedata directly without importing them
        
        EXAMPLE OF A WELL-WRITTEN FUNCTION:
        def normalize_phone(series):
            def clean(val):
                if pd.isna(val) or str(val).strip() == '':
                    return val
                digits = re.sub(r'\\D', '', str(val))
                return digits[:16]
            return series.apply(clean)

        EXISTING TOOLKIT (do not duplicate):
        {json.dumps(toolkit_keys, indent=2)}

        COLUMNS NEEDING FUNCTIONS:
        {json.dumps(needs_function_generation, indent=2)}

        For each column, the instruction tells you what the output should look like.
        The sample_values show you what the raw input looks like.
        Write the function to transform from that input format to the desired output.

        Return ONLY valid JSON with no explanation, no markdown, no code fences:
        [
            {{
                "function_name": "descriptive_snake_case_name",
                "column": "source_column_name",
                "code": "def descriptive_snake_case_name(series): ..."
            }}
        ]
    """

    fallback = []

    try:
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )
        
        text = resp.content[0].text
        text = text[text.find('['):text.rfind(']')+1]

        result = json.loads(text)
        logger.info(f"Generated {len(result)} cleaning function(s)")
        return result

    except json.JSONDecodeError as e:
        logger.error(f"generate_function returned invalid JSON: {e}")
        return fallback

    except Exception as e:
        logger.error(f"generate_function failed: {e}")
        return fallback


def apply_generated_functions(generated_functions: list, df: pd.DataFrame) -> dict:
    import re
    import unicodedata

    # whitelist — only these are available to generated code
    # modules are pre-imported so Claude's code can use them without import statements
    safe_globals = {
        "__builtins__": {
            "len": len, "str": str, "int": int, "float": float,
            "round": round, "range": range, "enumerate": enumerate,
            "isinstance": isinstance, "None": None, "True": True, "False": False,
            "list": list, "dict": dict, "set": set, "tuple": tuple,
            "map": map, "filter": filter, "zip": zip, "any": any, "all": all,
            "print": print
        },
        "pd": pd,
        "re": re,
        "unicodedata": unicodedata,
    }

    loaded = {}

    for item in generated_functions:
        function_name = item["function_name"]
        code          = item["code"]
        column        = item["column"]

        try:
            namespace = dict(safe_globals)

            # exec generated code into sandboxed namespace
            exec(code, namespace)

            func = namespace.get(function_name)
            if func is None:
                logger.warning(f"Function {function_name} not found after exec")
                continue

            # test on a small sample before storing — catches runtime errors early
            if column in df.columns:
                func(df[column].head(3))

            loaded[function_name] = func
            logger.info(f"Loaded generated function: {function_name}")

        except Exception as e:
            logger.error(f"Failed to load generated function {function_name}: {e}")
            continue

    return loaded

def run_correction(user_message: str, agent_result: dict) -> dict:
    client = _get_anthropic_client()

    # pull current state from cache
    current_mappings = agent_result.get("field_mappings", [])
    unmapped_columns = agent_result.get("unmapped_columns", [])
    business_context = agent_result.get("business_context", [])
    toolkit_keys     = list(get_cleaning_toolkit().keys())

    prompt = f"""
    You are an SAP data migration assistant helping a user correct their field mappings and cleaning rules.

    CURRENT FIELD MAPPINGS:
    {json.dumps(current_mappings, indent=2)}

    UNMAPPED COLUMNS (do not map these unless user explicitly asks):
    {json.dumps(unmapped_columns, indent=2)}

    AVAILABLE CLEANING FUNCTIONS:
    {json.dumps(toolkit_keys, indent=2)}

    EXISTING BUSINESS CONTEXT:
    {json.dumps(business_context, indent=2)}

    USER INSTRUCTION:
    {user_message}

    Parse the user's intent and return ONLY valid JSON:
    {{
        "updated_mappings": [...],
        "cleaning_instructions": [
            {{
                "column": "source_column_name",
                "instruction": "what the user wants done",
                "generate_function": true/false
            }}
        ],
        "business_context": ["any domain rules or context the user provided"],
        "excluded_columns": ["columns the user wants removed"],
        "confirmation": "one sentence — what you understood and applied",
        "unresolved": ["anything you could not confidently act on"]
    }}

    Rules:
    - Only change mappings the user explicitly mentions
    - Set generate_function to true if the cleaning instruction requires a function not in available toolkit
    - If nothing changed in a category, return an empty array for that field
    """

    # safe fallback — preserves current state if Claude fails
    fallback = {
        "updated_mappings":      current_mappings,
        "cleaning_instructions": [],
        "business_context":      business_context,
        "excluded_columns":      [],
        "confirmation": "Could not apply correction. No changes made.",
        "unresolved":   [user_message]
    }

    try:
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        # strip any markdown fences Claude may have added
        text = resp.content[0].text
        text = text[text.find('{'):text.rfind('}')+1]

        result = json.loads(text)
        logger.info(result)
        # append new business context on top of existing — never overwrite
        result["business_context"] = business_context + result.get("business_context", [])
            
        # build confirmation echo — append unresolved items if any
        if result.get("unresolved"):
            result["confirmation"] += " Could not apply: " + ", ".join(result["unresolved"])

        logger.info(f"Correction applied: {result['confirmation']}")
        return result

    except json.JSONDecodeError as e:
        logger.error(f"Correction returned invalid JSON: {e}")
        return fallback

    except Exception as e:
        logger.error(f"Correction failed: {e}")
        return fallback


def run_agent(df: pd.DataFrame)-> str:
    client = _get_anthropic_client()
    columns = df.columns.tolist()
    sample_rows = df.head(5).to_dict(orient='records')
    toolkit_keys = list(get_cleaning_toolkit().keys())
    sap_types = list(SAP_SCHEMAS.keys())
    messages = [
        {
            "role": "user",
            "content": (f"""
                    You are an SAP S/4HANA data migration assistant.
                    Use the available tools to run diagnostics.
                    Attempt to map all of the columns to SAP fields. 
                    You may encounter issues with mapping some of it and you are able
                    to reattempt mapping 
                    You are being given two things:
                    1. A list of column names from a legacy ERP CSV export
                    2. 3 sample rows of actual data from that CSV
                    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    COLUMN NAMES
                    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    {json.dumps(columns, indent=2)}
                    SAMPLE ROWS (3 rows)
                    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    {json.dumps(sample_rows, indent=2, default=str)}

                    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    VALID SAP SCHEMA TYPES
                    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    {json.dumps(sap_types, indent=2)}
                    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    AVAILABLE CLEANING FUNCTIONS
                    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    {json.dumps(toolkit_keys, indent=2)}
                    """)
                    
        }
    ]

    result = {}
    try:
        for i in range(5):
        # temporarily replaces while True loop with max 5 iterations
        # while True:
            response = client.messages.create(
                model = 'claude-sonnet-4-5',
                max_tokens = 2048,
                tools = agent_tools,
                messages=messages
            )
            logger.info(f"stop_reason: {response.stop_reason}")
            if response.stop_reason == 'end_turn':
                for block in response.content:
                    if hasattr(block,"text"):
                        result["summary"] = block.text
                break
            if response.stop_reason == 'tool_use':
                tool_results = []

                for block in response.content:
                    if block.type == 'tool_use':

                        output = execute_tool(df, block.name, block.input)
                        result[block.name] = output

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content" : json.dumps(output, default=str)
                        })
                messages.append({"role": "assistant", "content": response.content })
                messages.append({"role": "user", "content": tool_results })
        return result
    except Exception as e:
        logger.error(f"Agent loop failed: {e}")
        return {
            "detect_SAP_schema": {"success": False, "result": "customer"},
            "map_columns_to_sap_fields": {"success": False, "result": {
                "field_mappings": [],
                "unmapped_columns": df.columns.tolist()
            }},
            "final_summary": "Analysis failed. Please retry or contact support.",
            "agent_failed": True
        }




def _get_anthropic_client() -> Anthropic:

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set in .env")
    return Anthropic(api_key=api_key)