from __future__ import annotations

import os
import uuid
from typing import Optional
import csv
import pycountry
import pandas as pd
import re
from collections import Counter

def load_legacy_csv(csv_path: str) -> pd.DataFrame:
    """
    Load a messy legacy business CSV into a DataFrame.

    Intended behavior:
    - Read CSV with robust defaults (encoding, separators, bad lines)
    - Preserve raw columns for traceability
    - Return a DataFrame for subsequent cleaning
    """

    try:
        ##pd.read_csv is a function that handles the file opening, readingg, header detection
        ##delimter parsing, and dataframe all in one
        return pd.read_csv(csv_path, encoding='utf-8')
    except FileNotFoundError:
        print("File not found:", csv_path)
        return pd.DataFrame()


def clean_legacy_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and transform the legacy data into a migration-ready shape.

    Intended behavior (examples):
    - Normalize headers (trim, snake_case, dedupe)
    - Coerce datatypes (dates, numbers)
    - Standardize codes (country, currency, units)
    - Handle missing values and obvious outliers
    - Create derived fields required by target SAP structures
    - Return a cleaned DataFrame
    """
    customer_map = {
        "cust_id": "Customer_ID",
        "customerid": "Customer_ID",
        "custid": "Customer_ID",
        "full name": "Customer Name",
        "fullname": "Customer Name",
        "full_name": "Customer Name",
        "full_name": "Customer Name",
        "phone": "Phone",
        "PHONE": "Phone",
        "Email": "Email",
        "e_mail": "Email",
        "cntry": "Country",
        "contry": "Country",
        "country": "Country",
        "country_name": "Country",
        "country_name": "Country",
        "anual_revnue": "Annual Revenue"
    }
    ## drops row duplicates (keeps one)
    df = df.drop_duplicates() 
    print("Raw columns:", df.columns.tolist())

    #rename the columns to the new names under customer_map
    df.columns = [str(col).strip() for col in df.columns]

    df = df.rename(columns=customer_map)
    print("Columns after rename:", df.columns.tolist())  # ← add this

    required = ["Customer_ID", "Customer Name", "Phone", "Email", "Country", "Annual Revenue"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"CSV is missing required columns (after mapping): {missing}. "
            f"Expected one of: cust_id/customerid, full name/fullname, phone, email, country/cntry, anual_revnue."
        )

    df['Annual Revenue'] = df['Annual Revenue'].astype(str)
    df['Annual Revenue'] = df['Annual Revenue'].str.replace('[$,]', '', regex=True)
    ## converts to annual revenue data typevalue into a number
    df['Annual Revenue'] = pd.to_numeric(df['Annual Revenue'], errors='coerce')

    ## standardize the country column by calling standardize_Country function
    df['Country'] = df['Country'].apply(standardize_country)
    ## standardize the currency to USD
    df['Currency'] = 'USD'
    ## creates a hashmap of all customer_id to check for duplicates later
    id_counts = Counter(df['Customer_ID'])

    ## if no issues, set as 'READY' else 'FLAGGED'
    def get_status(row):
        if pd.isna(row['Customer_ID']) or pd.isna(row['Customer Name']) or pd.isna(row['Phone']) or pd.isna(row['Email']):
            return 'FLAGGED'
        return 'READY'
    ## validates data and adds it as a note
    def normalize_phone(row):
        if pd.isna(str(row['Phone'])):
            return ''
        return re.sub(r'\D', '', str(row['Phone']))
    def get_status_and_notes(row):
        issues = []
        phone_number = str(row['Phone']) # convert to string or it will cause re to crash
        email = row['Email']
        customer_id = row['Customer_ID']
        flag = False
        if pd.notna(phone_number):
            phone_number_digits_only = re.sub(r'\D', '', phone_number)
            phone_num_length = len(phone_number_digits_only)
            if phone_num_length != 10:
                issues.append("Phone Number is invalid")
        if pd.notna(email):
            if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
                issues.append("Email is invalid")
        if pd.notna(customer_id):
            if id_counts[customer_id] > 1:
                issues.append("Multiple customer ids exists")
        if pd.isna(row['Customer_ID']) or pd.isna(row['Customer Name']) or pd.isna(row['Phone']) or pd.isna(row['Email']) or pd.isna(row["Country"]) or pd.isna(row["Annual Revenue"]):
            flag = True
        if pd.isna(row['Customer_ID']):
            issues.append("Missing Customer_ID")
        if pd.isna(row["Customer Name"]):
            issues.append("Missing Customer_name")
        if pd.isna(row["Phone"]):
            issues.append("Missing Phone Number")
        if pd.isna(row["Email"]):
            issues.append("Missing Email")
        if pd.isna(row["Country"]):
            issues.append("Missing Country")
        if pd.isna(row["Annual Revenue"]):
            issues.append("Missing Annual Revenue")
        
        notes = ', '.join(issues)
        status = 'FLAGGED' if (len(issues) or flag) else 'READY'
        return pd.Series({'Migration_Status': status, 'Notes': notes})

    df['Phone'] = df.apply(normalize_phone, axis = 1)
    ## goes through every single row and flags if a value is missing
    ## goes through values and checks if it's an outlier (also known as numbers that should not be possible like age must be >= 0)
    df[['Migration_Status', 'Notes']] = df.apply(get_status_and_notes, axis=1)
    ## this replaces empty cells with "MISSING VALUE" to highlight areas
    df = df.fillna('MISSING VALUE')

    return df


def write_clean_excel(
    df: pd.DataFrame,
    output_dir: Optional[str] = None,
    filename: Optional[str] = None,
) -> str:
    """
    Write the cleaned DataFrame to an Excel file in `outputs/`.

    Intended behavior:
    - Choose output directory (default: project `outputs/`)
    - Generate a unique filename if none provided
    - Write one or more worksheets (clean data, metadata, etc.)
    - Return absolute path to written Excel file
    """
    base_dir = os.path.dirname(os.path.dirname(__file__))
    resolved_output_dir = output_dir or os.path.join(base_dir, "outputs")
    os.makedirs(resolved_output_dir, exist_ok=True)

    resolved_filename = filename or f"cleaned_{uuid.uuid4().hex}.xlsx"
    out_path = os.path.join(resolved_output_dir, resolved_filename)

    df.to_excel(out_path, index = False)
    return out_path


import re
import pycountry

def strip_currency(series):
    def convert(value):
        if not value or str(value).strip() == '':
            return 'MISSING VALUE'
        return re.sub(r'[$,\s]', '', str(value)).strip()
    return series.apply(convert)


def normalize_phone(series):
    def convert(value):
        if not value or str(value).strip() == '':
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
        if not value or str(value).strip() == '':
            return 'MISSING VALUE'
        value = str(value).strip().lower()
        # Must have exactly one @ with something on both sides and a dot after @
        if re.match(r'^[^@]+@[^@]+\.[^@]+$', value):
            return value
        return 'INVALID'
    return series.apply(convert)


def strip_whitespace(series):
    def convert(value):
        if not value or str(value).strip() == '':
            return 'MISSING VALUE'
        return str(value).strip()
    return series.apply(convert)


def normalize_id(series):
    def convert(value):
        if not value or str(value).strip() == '':
            return 'MISSING VALUE'
        value = str(value).strip().upper()
        # Zero-pad to 10 characters if numeric
        if value.isdigit():
            return value.zfill(10)
        return value
    return series.apply(convert)


def flag_missing(series):
    def convert(value):
        if not value or str(value).strip() == '':
            return 'MISSING VALUE'
        return str(value).strip()
    return series.apply(convert)


def standardize_country(series):
    def convert(value):
        if not value or str(value).strip() == '':
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
    import math
    def convert(value):
        if value is None:
            return 'MISSING VALUE'
        if isinstance(value, float) and math.isnan(value):
            return 'MISSING VALUE'
        value = str(value).strip()
        if value == '' or value.lower() == 'nan':
            return 'MISSING VALUE'
        return value.title()
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

def dynamic_cleaning(df: pd.DataFrame, mapping_instructions: dict) -> pd.DataFrame:
    toolkit = get_cleaning_toolkit()
    res = pd.DataFrame()
    ##extracts response from claude
    result = pd.DataFrame()
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
    required = {'KUNNR', 'NAME1'}
    mapped_targets = set()
    for m in mapping_instructions['field_mappings']:
        mapped_targets.add(m['target'])
    low_confidence = False
    for m in mapping_instructions['field_mappings']:
        if m['confidence'] < 0.80:
            low_confidence = True
            break
    # maps each result to whether it should be blocked, needs review, or is ready.
    if not required.issubset(mapped_targets):
        result['Migration_Status'] = 'BLOCKED'
    elif low_confidence:
        result['Migration_Status'] = 'NEEDS_REVIEW'
    else:
        result['Migration_Status'] = 'READY'
    return result

        





if __name__ == "__main__":
    df = load_legacy_csv("uploads/data_sample.csv")
    print("Raw columns:", df.columns.tolist())
    cleaned = clean_legacy_dataframe(df)
    print(cleaned)