#Demo

Youtube link: https://youtu.be/xVY-kSFzh08


# MapAI — SAP Data Migration with AI integration

MapAI is a prototype that uses Claude AI to automate the SAP S/4HANA data migration process. Upload a legacy CSV file and the tool will automatically detect what type of SAP master data it contains, map each column to the correct SAP field, apply appropriate data cleaning, and generate a migration readiness report.

---

## The Problem

Companies upgrading to SAP S/4HANA issues with years of legacy data stored in formats that SAP simply won't accept. Customer IDs need to be 10-digit zero-padded numbers. Country values must be ISO 2-letter codes. Revenue fields cannot contain dollar signs or commas. Phone numbers must follow a single consistent format.

A consultant migrating this data manually such as renaming columns, reformatting values, validating every row which can take days or weeks on a single dataset. After all that effort, human error is still inevitable.

---

## What It Does

Upload a legacy CSV and MapAI will:

- **Detect the data type** — customer, vendor, material, or employee
- **Map every column** to the correct SAP field with a confidence score
- **Clean the data** row by row using format-specific rules
- **Flag low-confidence mappings** for consultant review instead of silently applying them
- **Generate a color-coded Excel file** and an AI audit report

**Cleaning examples:**

| Raw Value | Function | Result |
|-----------|----------|--------|
| `(555) 123-4567` / `555.123.4567` / `+1-555-123-4567` | normalize_phone | `+15551234567` |
| `USA` / `United States` / `usa` | standardize_country | `US` |
| `$1,000` / `$1,200.00` | strip_currency | `1000` / `1200.00` |
| `JOHN SMITH` | normalize_name | `John Smith` |
| ` Bob ` | strip_whitespace | `Bob` |

---

## How It Works

**1. Upload a CSV file**
The tool accepts any legacy CSV export.

**2. Claude detects the schema**
Claude reads the column names and 3 sample rows and determines whether the data is customer, vendor, material, or employee data. If detection is uncertain, it defaults to customer.

**3. Claude maps the columns**
Claude maps each source column to the correct SAP field and selects a cleaning function based on the column name and sample values.

Each mapping is assigned a confidence score between 0.0 and 1.0:

| Confidence | Meaning | Action |
|------------|---------|--------|
| 0.90 – 1.00 | Column name and data values clearly align | Applied automatically |
| 0.80 – 0.89 | Contextual inference from data values | Applied automatically |
| Below 0.80 | Column name or data is ambiguous | Flagged for consultant review |

For example, a column named `anual_revnue` containing values like `$500000` maps to `UMSAV` at 0.90 confidence — the typo is obvious but the data makes the intent clear. A column named `ref` with no clear data pattern might map at 0.60 and get flagged rather than applied.

**4. Python cleans the data**
Claude's mapping instructions are executed row by row locally. Phone numbers, country codes, currency values, and names are normalized to SAP-compatible formats using a fixed set of cleaning functions.

**5. Every row gets a migration status**
Each record is tagged based on mapping confidence and data completeness:

| Status | Condition |
|--------|-----------|
| ✅ READY | All required fields mapped above 80% confidence, no missing values |
| 🟡 NEEDS_REVIEW | One or more mappings below 80% confidence |
| 🟠 FLAGGED | A required field is present but contains an invalid or missing value |
| 🔴 BLOCKED | A required SAP field could not be mapped at all |

**6. Download the output**
A color-coded Excel file is generated alongside an AI-generated audit report summarizing what was mapped, the confidence level of each mapping, and which records or columns need consultant attention before loading into SAP.

---

## What This Project Currently Supports

MapAI is scoped to four SAP master data object types:

| Object Type | SAP Table | Typical Source Data |
|-------------|-----------|-------------------|
| Customer | KNA1 | CRM exports, billing systems, customer lists |
| Vendor | LFA1 | Procurement systems, AP exports, supplier lists |
| Material | MARA / MAKT | Product catalogs, inventory exports, item lists |
| Employee | PA0001 / PA0002 | HR systems, payroll exports, org charts |

These four object types were chosen because they are among the most commonly migrated master data records in SAP S/4HANA projects. Each schema is based on the actual SAP table field definitions sourced from [sapdatasheet.org](https://www.sapdatasheet.org).

The cleaning toolkit covers the most common data quality issues found in these object types: phone normalization, country standardization, currency stripping, name casing, and ID zero-padding. It does not enforce every SAP domain rule and is not a substitute for a full SAP data validation layer.

Does not currently support:
- Financial master data
- Sales or purchasing documents
- Mixed files containing multiple object types
- Custom SAP object types
- Enterprise-scale file processing

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, Tailwind CSS |
| Backend | Flask (Python) |
| Data processing | Pandas, openpyxl |
| AI | Claude Opus via Anthropic API |
| Utilities | pycountry, python-dotenv |

---

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+
- An [Anthropic API key](https://console.anthropic.com/)

### 1. Clone the repo
```bash
git clone https://github.com/your-username/data-project-1.git
cd data-project-1/ai-migration-tool
```

### 2. Set up the backend
```bash
pip install -r requirements.txt
```

Create a `.env` file in `ai-migration-tool/`:
```
ANTHROPIC_API_KEY=your_api_key_here
```

Start the Flask server:
```bash
python app.py
```

### 3. Set up the frontend
```bash
cd client
npm install
npm run dev
```

### 4. Open the app
Visit [http://localhost:3000](http://localhost:3000)

---

## Project Structure

```
ai-migration-tool/
├── app.py                  # Flask entry point
├── requirements.txt
├── routes/
│   ├── upload.py           # POST /api/upload
│   ├── analyze.py          # POST /api/analyze
│   └── download.py         # GET  /api/download
├── services/
│   ├── claude_service.py   # Claude API integration
│   ├── cleaner.py          # Data cleaning functions
│   └── sap_schemas.py      # SAP field definitions
└── client/                 # React frontend
    └── src/
        ├── App.jsx
        └── components/
            ├── FileUpload.jsx
            ├── DataTable.jsx
            └── AuditReport.jsx
```
