# SAP schema source
# KNA1: https://www.sapdatasheet.org/abap/tabl/kna1.html
# LFA1: https://www.sapdatasheet.org/abap/tabl/lfa1.html
# MARA: https://www.sapdatasheet.org/abap/tabl/mara.html
# PA0001: https://www.sapdatasheet.org/abap/tabl/pa0001.html
# PA0002: https://www.sapdatasheet.org/abap/tabl/pa0002.html


# Source: https://www.sapdatasheet.org/abap/tabl/kna1.html
SAP_CUSTOMER_SCHEMA = {
    "KUNNR":     "Customer Number — CHAR(10), zero-padded",
    "NAME1":     "Customer Name Primary — CHAR(35), required",
    "NAME2":     "Customer Name Secondary / DBA — CHAR(35), optional",
    "TELF1":     "Phone Number Primary — CHAR(16)",        
    "TELFX":     "Fax Number — CHAR(31)",
    "SMTP_ADDR": "Email Address — from ADR6 via ADRNR — CHAR(241)",
    "STRAS":     "Street Address — CHAR(35)",
    "ORT01":     "City — CHAR(35)",
    "PSTLZ":     "Postal Code / ZIP — CHAR(10)",
    "REGIO":     "Region / State Code — CHAR(3)",
    "LAND1":     "Country Key — CHAR(3), ISO 2-letter, required",
    "UMSAV":     "Annual Revenue — numeric, no currency symbol",
    "WAERS":     "Currency Code — CHAR(5) e.g. USD, EUR",
    "KDGRP":     "Customer Group / Segment — CHAR(2)",
    "AUFSD":     "Order Block Flag — CHAR(2), blank=active",
}

# Source: https://www.sapdatasheet.org/abap/tabl/lfa1.html
SAP_VENDOR_SCHEMA = {
    "LIFNR":     "Vendor Number — CHAR(10), zero-padded, required",
    "NAME1":     "Vendor Name Primary — CHAR(35), required",
    "NAME2":     "Vendor Name Secondary — CHAR(35), optional",
    "TELNR":     "Phone Number — CHAR(16)",
    "SMTP_ADDR": "Email Address — from ADR6 via ADRNR — CHAR(241)",
    "STRAS":     "Street Address — CHAR(35)",
    "ORT01":     "City — CHAR(35)",
    "PSTLZ":     "Postal Code / ZIP — CHAR(10)",
    "LAND1":     "Country Key — CHAR(3), ISO 2-letter, required",
    "WAERS":     "Currency Code — CHAR(5)",
    "ZTERM":     "Payment Terms Key — CHAR(4) e.g. NT30, NT60",
    "SPERM":     "Purchasing Block Flag — CHAR(1), blank=active, X=blocked",
}

# Source: https://www.sapdatasheet.org/abap/tabl/mara.html
# Note: MAKTX description text lives in MAKT table, joined via MATNR
SAP_MATERIAL_SCHEMA = {
    "MATNR":     "Material Number — CHAR(18), required",
    "MAKTX":     "Material Description — CHAR(40), from MAKT table",
    "MATKL":     "Material Group — CHAR(9)",
    "MEINS":     "Base Unit of Measure — UNIT(3) e.g. EA, KG, LB",
    "MTART":     "Material Type — CHAR(4), FERT/ROH/HALB",
    "MBRSH":     "Industry Sector — CHAR(1), M=Mechanical E=Electrical",
    "NTGEW":     "Net Weight — QUAN(13,3), numeric",
    "BRGEW":     "Gross Weight — QUAN(13,3), numeric",
    "GEWEI":     "Weight Unit — UNIT(3) e.g. KG, LB",
    "VOLUM":     "Volume — QUAN(13,3), numeric",
    "VOLEH":     "Volume Unit — UNIT(3) e.g. L, GAL",
}

# Source: https://www.sapdatasheet.org/abap/tabl/pa0001.html (org fields)
#         https://www.sapdatasheet.org/abap/tabl/pa0002.html (personal fields)
# Note: PA0001 = Org Assignment, PA0002 = Personal Data — both needed for full employee record
SAP_EMPLOYEE_SCHEMA = {
    "PERNR":     "Personnel Number — NUMC(8), zero-padded, required (PA0001)",
    "VORNA":     "First Name — CHAR(40), required (PA0002)",
    "NACHN":     "Last Name — CHAR(40), required (PA0002)",
    "GBDAT":     "Date of Birth — DATS(8), YYYYMMDD (PA0002)",
    "BEGDA":     "Hire / Start Date — DATS(8), begin date of org assignment (PA0001)",
    "PLANS":     "Position — NUMC(8), position code (PA0001)",
    "ORGEH":     "Organizational Unit — NUMC(8) (PA0001)",
    "STELL":     "Job Code — NUMC(8) (PA0001)",
    "WERKS":     "Personnel Area — CHAR(4) (PA0001)",
    "MOLGA":     "Country Grouping — CHAR(2), 01=USA 02=Canada (PA0001)",
    "ANSVH":     "Employment Percentage — DEC(5,2), 100=full-time (PA0001)",
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
        "label":    "SAP Material Master (MARA/MAKT)"
    },
    "employee": {
        "schema":   SAP_EMPLOYEE_SCHEMA,
        "required": {"PERNR", "VORNA", "NACHN"},
        "label":    "SAP Employee Master (PA0001/PA0002)"
    },
}