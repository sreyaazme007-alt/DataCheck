# DataCheck — Data Import Error Detector

**DataCheck** is an automated data integrity validation system built with Python, Flask, and SQLite. It serves as a pre-import firewall for relational database systems, scanning incoming CSV datasets row-by-row to detect missing values, primary key collisions, duplicate records, data type anomalies, regex format violations, and domain range breaches before corrupted data reaches production databases.

---

## 1. Project Abstract

In enterprise software engineering, database management systems (DBMS), and data analytics pipelines, corrupted or improperly formatted data introduces costly downstream defects (the classic *Garbage-In, Garbage-Out* problem). Manual verification of large datasets is tedious, error-prone, and unscalable. 

**DataCheck** provides an automated, rule-based auditing engine that validates tabular datasets against strict domain constraints. It generates detailed diagnostic reports specifying the exact row number, column name, erroneous value, error classification, and concrete suggested corrections. Furthermore, it tracks full audit histories in an SQLite relational database and permits instant CSV report downloads for data remediation workflows.

---

## 2. Problem Statement

Organizations routinely ingest data through CSV exports originating from external partners, web forms, and legacy spreadsheets. Common issues include:
- Incomplete records with null or blank mandatory fields.
- Duplicate primary keys that violate relational database entity integrity constraints.
- Type mismatches (e.g., text strings accidentally entered into numeric age or GPA fields).
- Out-of-range anomalies (e.g., negative ages, impossible GPAs exceeding 10.00).
- Malformed strings violating standard formats (e.g., invalid email addresses, non-standard date notations).

Without an automated detector, loading such files into a database causes transaction rollbacks, pipeline crashes, or data corruption.

---

## 3. Project Objectives

1. **Automate Ingestion Integrity**: Provide an easy-to-use web interface for instant CSV dataset validation.
2. **Deterministic Rule Validation**: Implement transparent, algorithmic checks ($O(N)$ row scan, $O(1)$ set lookups) without unpredictable black-box models or machine learning.
3. **Structured Diagnostics**: Present actionable remediation guidance (Row Number, Column, Value, Error Type, Suggested Fix).
4. **Relational Audit Trail**: Store every validation session and granular error records in an SQLite database.
5. **Remediation Export**: Enable users to download validation logs as structured CSV files.

---

## 4. Key Features

- **Drag-and-Drop CSV Upload**: Safe upload mechanism handling empty files, malformed syntax, and size restrictions (up to 16 MB).
- **Missing Value Detection**: Identifies blank cells, empty strings, and null placeholders across all required columns.
- **Uniqueness & Duplicate Detection**:
  - Catches duplicate primary keys (`Student_ID`).
  - Detects duplicate entire rows using tuple hashing.
- **Data Type & Format Verification**:
  - Validates integer data types for `Student_ID` and `Age`.
  - Validates floating-point numbers for `CGPA`.
  - Validates RFC-compliant email formats using Regular Expressions.
  - Validates standard ISO-8601 calendar dates (`YYYY-MM-DD`).
- **Domain Range Checks**:
  - `Age`: Constrained between `16` and `100`.
  - `CGPA`: Constrained between `0.00` and `10.00`.
- **Predefined Category Validation**: Enforces allowed Department codes (`CSE`, `ECE`, `IT`, `MECH`, `CIVIL`, `AIDS`).
- **Interactive Dashboard**:
  - Real-time metric cards (Total Rows, Valid Rows, Invalid Rows, Errors Count).
  - Categorical error distribution chips.
  - Dynamic client-side search and error type filtering.
- **CSV Report Export**: Downloadable remediation report for spreadsheet workflows.
- **SQLite Audit History**: View, review, or delete historical validation runs.
- **Built-in Sample Dataset**: One-click download of `sample_data.csv` containing both valid and intentionally flawed records for quick testing.

---

## 5. Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Backend** | Python 3.12 | Core validation logic, regex parsing, and algorithms |
| **Web Framework** | Flask 3.1 | Routing, template rendering, and file upload processing |
| **Database** | SQLite 3 | Embedded ACID-compliant database for runs and error logs |
| **Frontend** | HTML5, CSS3, Vanilla JS | Modern responsive UI, drag-and-drop dropzone, live table filter |
| **Testing** | Python `unittest` | Automated test suite for validation rules and endpoints |

---

## 6. Core Algorithms & Data Structures

- **Hash Sets for Uniqueness ($O(1)$ average lookup)**:
  - `seen_ids`: A Python `set` storing primary key identifiers. When a new row is scanned, the ID is checked in $O(1)$ time. If present, a `Duplicate ID` error is logged.
  - `seen_rows`: A Python `set` storing hashable tuples of entire row values to detect full duplicate records in $O(1)$ time.
- **Regular Expression Pattern Matching**:
  - `EMAIL_REGEX`: `^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$` ensures email strings adhere to standard syntactic structures.
  - `NAME_REGEX`: `^[a-zA-Z\s.'-]+$` validates personal names while permitting hyphens and initials.
- **Single-Pass Linear Scan ($O(N)$ Time Complexity)**:
  - The dataset is processed in a single pass of $N$ data rows, ensuring optimal memory and processing time suitable for standard datasets.
- **Relational Integrity via Cascading Foreign Keys**:
  - The SQLite database links `validation_errors` to `validation_runs` with `ON DELETE CASCADE`, ensuring no orphaned error records when a run is removed.

---

## 7. Project Structure

```text
DataCheck/
│
├── app.py                  # Main Flask application, routes, and validation engine
├── requirements.txt        # Python dependency manifest (Flask, Werkzeug)
├── sample_data.csv         # Demonstration dataset with valid & invalid records
├── test_app.py             # Automated unit & integration test suite
├── datacheck.db            # SQLite database (auto-created on startup)
├── README.md               # Comprehensive project documentation
│
├── templates/              # Jinja2 HTML templates
│   ├── base.html           # Base layout with navbar, alerts, and footer
│   ├── landing.html        # Attractive landing page with hero & feature cards
│   ├── index.html          # Dashboard, upload area, and rules card (/dashboard)
│   ├── results.html        # Detailed report view with error table & filters
│   └── history.html        # Historical log of previous validation runs
│
└── static/                 # Static frontend assets
    ├── style.css           # Clean, modern stylesheet & animations
    ├── main.js             # Client-side dropzone & dynamic table filtering
    ├── css/style.css       # Mirrored CSS stylesheet
    └── js/main.js          # Mirrored JavaScript file
```

---

## 8. Installation & Run Guide (Windows / Local)

### Step 1: Open PowerShell or Command Prompt
Open your terminal and navigate to the project directory:
```powershell
cd c:\Users\SREYA\OneDrive\Documents\DataCheck
```

### Step 2: Install Dependencies
Install the required packages using Python's package manager:
```powershell
py -m pip install -r requirements.txt
```

### Step 3: Run the Automated Tests (Optional but Recommended)
Run the built-in test suite to confirm all checks pass:
```powershell
py test_app.py
```
*Expected output: `Ran 4 tests ... OK`*

### Step 4: Start the Flask Application
Run the application server:
```powershell
py app.py
```

### Step 5: Open in Your Web Browser
Open your web browser and navigate to:
```text
http://127.0.0.1:5000
```

---

## 9. How to Demonstrate During a Presentation

1. **Attractive Landing Page**: Open `http://127.0.0.1:5000/`. Highlight the bold **DataCheck** title, subtitle, mission description, and the 4 core feature cards (Missing Value Detection, Duplicate Record Detection, Invalid Data Detection, and Detailed Validation Reports).
2. **Get Started**: Click the prominent **Get Started** button to navigate smoothly to the CSV Upload Dashboard at `/dashboard`.
3. **Download Sample Dataset**: Click the **Download Sample CSV** button on the navbar or upload card to inspect `sample_data.csv`.
4. **Upload & Analyze**: Drag and drop `sample_data.csv` into the upload box and click **Validate Dataset**.
5. **Inspect Validation Results**:
   - Point out the summary cards: Total Rows (16), Valid Rows (4), Invalid Rows (12), Total Errors (13).
   - Show how the mathematical identity holds: $\text{Total Rows} = \text{Valid Rows} + \text{Invalid Rows}$.
   - Review the categorized chips (Missing Value, Duplicate ID, Duplicate Record, Invalid Type, Out of Range, Invalid Format, Invalid Category).
6. **Interactive Filtering**: Type `Age` or select an error type from the dropdown to demonstrate real-time table filtering.
7. **Export Report**: Click **Download Report (.csv)** to show the generated CSV error log.
8. **Validation History**: Navigate to **Validation History** to demonstrate SQLite persistence across user sessions.

---

## 10. Sample Test Dataset Walkthrough

The included `sample_data.csv` tests all required validation rules:

| Row # | Issue Injected | Error Detected | Suggested Correction |
|---|---|---|---|
| **Row 4** | Missing Email | `Missing Value` | Enter a valid student email address. |
| **Row 5** | Missing Name | `Missing Value` | Enter the student's complete name. |
| **Row 6** | `vikram.singh_at_example.com` | `Invalid Format` | Format as user@domain.com (missing `@`). |
| **Row 7** | Age = `"twenty"` | `Invalid Type` | Age must be a numeric integer value. |
| **Row 8** | CGPA = `12.50` | `Out of Range` | CGPA must be between 0.00 and 10.00. |
| **Row 9** | Age = `-5` | `Out of Range` | Age must be between 16 and 100. |
| **Row 10**| Department = `"ROBOTICS"` | `Invalid Category` | Department must be one of: CSE, ECE, IT, MECH, CIVIL, AIDS. |
| **Row 11**| Date = `"15-08-2023"` | `Invalid Format` | Date must match ISO 8601: `YYYY-MM-DD`. |
| **Row 12**| Duplicate Student_ID `102` | `Duplicate ID` | Primary key collision with Row 3. |
| **Row 13**| Exact duplicate of Row 2 | `Duplicate Record` | Full row match detected via tuple hashing. |
| **Row 15**| CGPA = `-1.50` | `Out of Range` | CGPA must be between 0.00 and 10.00. |
| **Row 16**| `siddharth@example` | `Invalid Format` | Missing top-level domain extension. |

---

## 11. Limitations & Future Scope

### Limitations:
- The validation schema currently defaults to the standard Academic Admissions schema.
- Processes single CSV files synchronously rather than asynchronous worker queues.
- Maximum file size is capped at 16 MB to prevent memory exhaustion on local setups.

### Future Enhancements:
- **Custom Schema Builder**: Allow users to define custom column rules and upload schemas via a JSON configurator.
- **Excel (.xlsx) & JSON Ingestion**: Add support for parsing multi-sheet Excel workbooks and JSON arrays.
- **Auto-Correction Engine**: Automatically trim whitespace, convert dates, and format phone numbers with user approval before database commit.
