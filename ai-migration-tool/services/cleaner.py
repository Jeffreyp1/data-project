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
def standardize_country(value):
    try:
        country = pycountry.countries.search_fuzzy(value)[0]
        return country.alpha_2
    except:
        return value

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
        "anual_revnue": "Annual Revenue",
    }
    ## drops row duplicates (keeps one)
    df = df.drop_duplicates() 
    #rename the columns to the new names under customer_map
    df = df.rename(columns=customer_map)
    df['Annual Revenue'] = df['Annual Revenue'].astype(str).str.replace('[$,]', '', regex=True)
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
        phone_number = str(row['Phone'])
        if pd.notna(phone_number):
            phone_number_digits_only = re.sub(r'\D', '', phone_number)
        return phone_number_digits_only
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

    # TODO: actually write excel via pandas/openpyxl
    return out_path

if __name__ == "__main__":
    df = load_legacy_csv("uploads/data_sample.csv")
    cleaned = clean_legacy_dataframe(df)
    print(cleaned)