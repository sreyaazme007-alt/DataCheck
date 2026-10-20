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

