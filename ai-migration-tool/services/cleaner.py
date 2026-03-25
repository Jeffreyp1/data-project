from __future__ import annotations

import os
import uuid
from typing import Optional
import csv
import pycountry
import pandas as pd
import re
from collections import Counter
import logging
logger = logging.getLogger(__name__)
def load_legacy_csv(csv_path: str) -> pd.DataFrame:
    try:
        import io
        with open(csv_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # Quote unquoted currency values like $1,000 or $1,234.56 so the comma
        # inside them isn't treated as a CSV field delimiter by pandas
        content = re.sub(r'(?<!["\w])\$[\d,]+(?:\.\d+)?', lambda m: f'"{m.group()}"', content)
        return pd.read_csv(io.StringIO(content))
    except FileNotFoundError:
        logger.error(f"File not found: {csv_path}")
        return pd.DataFrame()




def write_clean_excel(
    df: pd.DataFrame,
    output_dir: Optional[str] = None,
    filename: Optional[str] = None,
) -> str:
    base_dir = os.path.dirname(os.path.dirname(__file__))
    resolved_output_dir = output_dir or os.path.join(base_dir, "outputs")
    os.makedirs(resolved_output_dir, exist_ok=True)

    resolved_filename = filename or f"cleaned_{uuid.uuid4().hex}.xlsx"
    out_path = os.path.join(resolved_output_dir, resolved_filename)

    df.to_excel(out_path, index = False)
    return out_path


import re
import math
import pycountry

def _is_missing(value):
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    if str(value).strip().lower() in ('', 'nan'):
        return True
    return False


def strip_currency(series):
    def convert(value):
        if _is_missing(value):
            return 'MISSING VALUE'
        return re.sub(r'[$,\s]', '', str(value)).strip()
    return series.apply(convert)


def normalize_phone(series):
    def convert(value):
        if _is_missing(value):
            return 'MISSING VALUE'
        digits = re.sub(r'\D', '', str(value))
        # Strip leading country code if already 11 digits starting with 1
        if len(digits) == 11 and digits.startswith('1'):
            digits = digits[1:]
        if len(digits) == 10:
            return f'+1{digits}'
        return 'INVALID'
    return series.apply(convert)


def normalize_email(series):
    def convert(value):
        if _is_missing(value):
            return 'MISSING VALUE'
        value = str(value).strip().lower()
        # Must have exactly one @ with something on both sides and a dot after @
        if re.match(r'^[^@]+@[^@]+\.[^@]+$', value):
            return value
        return 'INVALID'
    return series.apply(convert)


def strip_whitespace(series):
    def convert(value):
        if _is_missing(value):
            return 'MISSING VALUE'
        return str(value).strip()
    return series.apply(convert)


def normalize_id(series):
    def convert(value):
        if _is_missing(value):
            return 'MISSING VALUE'
        value = str(value).strip().upper()
        # Zero-pad to 10 characters if numeric
        if value.isdigit():
            return value.zfill(10)
        return value
    return series.apply(convert)


def flag_missing(series):
    def convert(value):
        if _is_missing(value):
            return 'MISSING VALUE'
        return str(value).strip()
    return series.apply(convert)


def standardize_country(series):
    def convert(value):
        if _is_missing(value):
            return 'MISSING VALUE'
        value = str(value).strip()
        if len(value) == 2:
            match = pycountry.countries.get(alpha_2=value.upper())
            if match:
                return match.alpha_2
        if len(value) == 3:
            match = pycountry.countries.get(alpha_3=value.upper())
            if match:
                return match.alpha_2
        try:
            results = pycountry.countries.search_fuzzy(value)
            if results:
                return results[0].alpha_2
        except LookupError:
            pass
        return 'UNKNOWN'
    return series.apply(convert)

def normalize_name(series):
    def convert(value):
        if _is_missing(value):
            return 'MISSING VALUE'
        return str(value).strip().title()
    return series.apply(convert)
def get_cleaning_toolkit():
    return {
        'strip_currency':      strip_currency,
        'normalize_phone':     normalize_phone,
        'normalize_email':     normalize_email,
        'strip_whitespace':    strip_whitespace,
        'normalize_id':        normalize_id,
        'flag_missing':        flag_missing,
        'standardize_country': standardize_country,
        'normalize_name':      normalize_name,
    }

def dynamic_cleaning(df: pd.DataFrame, mapping_instructions: dict, required, extra_toolkit=None) -> pd.DataFrame:
    toolkit = get_cleaning_toolkit()

    if extra_toolkit:
        toolkit.update(extra_toolkit)
    ##extracts response from claude
    result = pd.DataFrame()
    logger.info(mapping_instructions)
    for mapping in mapping_instructions["field_mappings"]:
        source = mapping['source']
        target = mapping['target']
        cleaning_fn = mapping['cleaning_fn']
        confidence = mapping['confidence']
        ## ensure that claude did not hallucinate and change the original source mapping
        if source not in df.columns:
            continue
        ## if ensures that we do not add anything with low confidence level
        if confidence < 0.80:
            result[f'REVIEW___{target}'] = df[source]
            continue

        func = toolkit.get(cleaning_fn, toolkit['strip_whitespace'])
        result[target] = func(df[source])
    
    for col in mapping_instructions.get('unmapped_column', []):
        if col in df.columns:
            result[f'UNMAPPED__{col}'] = df[col]

    

    # below are required columns. if empty/null, automatically flag
    # required = {'KUNNR', 'NAME1'}
    mapped_targets = set()
    for m in mapping_instructions['field_mappings']:
        mapped_targets.add(m['target'])
    low_confidence = False
    for m in mapping_instructions['field_mappings']:
        if m['confidence'] < 0.80:
            low_confidence = True
            break
    statuses = []

    for index, row in result.iterrows():
        # original state. status will change depending on row values
        status = 'READY'
        if not required.issubset(mapped_targets):
            status = 'BLOCKED'
        else: 
            for field in required:
                if field in result.columns and (pd.isna(row[field]) or str(row[field]).strip() in ('MISSING VALUE', 'INVALID', 'nan', 'NAN', '')):
                    status = 'FLAGGED'
                    break
        if status == 'READY':
            for col in result.columns:
                if pd.isna(row[col]) or str(row[col]).strip() in ('MISSING VALUE', 'INVALID', 'nan', 'NAN', ''):
                    status = 'NEEDS_REVIEW'
                    break
        
    # maps each result to whether it should be blocked, needs review, or is ready.

        if low_confidence and status == 'READY':
            status= 'NEEDS_REVIEW'
        statuses.append(status)
    result['Migration_Status'] = statuses
    return result

        





# if __name__ == "__main__":
#     df = load_legacy_csv("uploads/data_sample.csv")
#     print("Raw columns:", df.columns.tolist())
#     cleaned = clean_legacy_dataframe(df)
#     print(cleaned)