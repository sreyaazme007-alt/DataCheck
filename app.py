"""
DataCheck — Data Import Error Detector
======================================
Core CSE Web Application for detecting data integrity errors in CSV imports.
Uses Flask, SQLite, and pure Python rule-based algorithms.
"""

import os
import re
import csv
import io
import sqlite3
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, send_file, Response, abort
)
from werkzeug.utils import secure_filename

# --- Application Configuration ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'datacheck-local-development-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload limit
DATABASE_PATH = os.environ.get('DATABASE_PATH', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'datacheck.db'))
os.makedirs(os.path.dirname(os.path.abspath(DATABASE_PATH)), exist_ok=True)
SAMPLE_CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sample_data.csv')

# Predefined Valid Schema Constraints for Academic Records
EXPECTED_COLUMNS = [
    'Student_ID',
    'Full_Name',
    'Email',
    'Age',
    'Department',
    'CGPA',
    'Enrollment_Date'
]

VALID_DEPARTMENTS = {'CSE', 'ECE', 'IT', 'MECH', 'CIVIL', 'AIDS'}
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
NAME_REGEX = re.compile(r"^[a-zA-Z\s.'-]+$")


# --- Database Helpers ---
def get_db():
    """Establish connection to SQLite database with foreign keys enabled."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Initialize database tables for validation runs and logged errors."""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS validation_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                uploaded_at TEXT NOT NULL,
                file_size_kb REAL NOT NULL,
                total_rows INTEGER NOT NULL,
                valid_rows INTEGER NOT NULL,
                invalid_rows INTEGER NOT NULL,
                total_errors INTEGER NOT NULL,
                status TEXT NOT NULL
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS validation_errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                row_number INTEGER NOT NULL,
                column_name TEXT NOT NULL,
                invalid_value TEXT,
                error_type TEXT NOT NULL,
                suggested_correction TEXT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES validation_runs (id) ON DELETE CASCADE
            );
        """)
        conn.commit()


# Ensure database tables exist upon module import
init_db()


# --- Validation Engine (Rule-based Core Algorithm) ---
def validate_csv(content_str):
    """
    Parses and validates CSV text against defined data integrity rules.
    
    Returns:
        dict: {
            'total_rows': int,
            'valid_rows': int,
            'invalid_rows': int,
            'total_errors': int,
            'errors': list of error dicts
        }
    """
    errors = []
    rows_with_errors = set()

    # Read CSV lines safely
    try:
        f = io.StringIO(content_str)
        reader = csv.reader(f)
        all_lines = [row for row in reader if any(cell.strip() for cell in row)]
    except Exception as e:
        return {
            'fatal_error': f"CSV Parsing Error: Malformed structure ({str(e)})"
        }

    if not all_lines:
        return {'fatal_error': "The uploaded CSV file is empty or contains only blank rows."}

    # Extract & validate header row
    raw_headers = all_lines[0]
    headers = [h.strip() for h in raw_headers]

    # Map headers to index for safe column lookups
    header_indices = {col.lower(): idx for idx, col in enumerate(headers)}
    missing_headers = [col for col in EXPECTED_COLUMNS if col.lower() not in header_indices]

    if missing_headers:
        return {
            'fatal_error': (
                f"Missing required columns in CSV header: {', '.join(missing_headers)}. "
                f"Expected columns: {', '.join(EXPECTED_COLUMNS)}"
            )
        }

    data_rows = all_lines[1:]
    total_rows = len(data_rows)

    if total_rows == 0:
        return {'fatal_error': "CSV contains column headers but zero data records."}

    seen_ids = set()
    seen_rows = set()

    for idx, row in enumerate(data_rows, start=2):  # Row 1 is header, so data starts at row 2
        row_has_error = False

        # Helper to get column value safely by expected column name
        def get_val(col_name):
            col_idx = header_indices.get(col_name.lower())
            if col_idx is not None and col_idx < len(row):
                return row[col_idx].strip()
            return ""

        # 1. Duplicate Row Detection (Entire row match)
        row_tuple = tuple(get_val(c) for c in EXPECTED_COLUMNS)
        if row_tuple in seen_rows:
            errors.append({
                'row_number': idx,
                'column_name': 'Entire Record',
                'invalid_value': ', '.join(row_tuple[:3]) + '...',
                'error_type': 'Duplicate Record',
                'suggested_correction': 'This entire row is identical to an earlier record. Remove the duplicate entry.'
            })
            row_has_error = True
        else:
            seen_rows.add(row_tuple)

        # 2. Student_ID Validation
        student_id_val = get_val('Student_ID')
        if not student_id_val:
            errors.append({
                'row_number': idx,
                'column_name': 'Student_ID',
                'invalid_value': student_id_val,
                'error_type': 'Missing Value',
                'suggested_correction': 'Provide a unique integer Student ID (e.g., 105).'
            })
            row_has_error = True
        else:
            try:
                sid_num = int(student_id_val)
                if sid_num <= 0:
                    errors.append({
                        'row_number': idx,
                        'column_name': 'Student_ID',
                        'invalid_value': student_id_val,
                        'error_type': 'Out of Range',
                        'suggested_correction': 'Student ID must be a positive integer greater than zero.'
                    })
                    row_has_error = True
                elif sid_num in seen_ids:
                    errors.append({
                        'row_number': idx,
                        'column_name': 'Student_ID',
                        'invalid_value': student_id_val,
                        'error_type': 'Duplicate ID',
                        'suggested_correction': f'Student ID {sid_num} is already assigned. Use a unique identifier.'
                    })
                    row_has_error = True
                else:
                    seen_ids.add(sid_num)
            except ValueError:
                errors.append({
                    'row_number': idx,
                    'column_name': 'Student_ID',
                    'invalid_value': student_id_val,
                    'error_type': 'Invalid Type',
                    'suggested_correction': 'Student ID must be a valid integer without letters or symbols.'
                })
                row_has_error = True

        # 3. Full_Name Validation
        name_val = get_val('Full_Name')
        if not name_val:
            errors.append({
                'row_number': idx,
                'column_name': 'Full_Name',
                'invalid_value': name_val,
                'error_type': 'Missing Value',
                'suggested_correction': "Enter the student's complete name."
            })
            row_has_error = True
        elif not NAME_REGEX.match(name_val):
            errors.append({
                'row_number': idx,
                'column_name': 'Full_Name',
                'invalid_value': name_val,
                'error_type': 'Invalid Format',
                'suggested_correction': 'Name should contain only alphabetic characters, spaces, and hyphens.'
            })
            row_has_error = True

        # 4. Email Validation
        email_val = get_val('Email')
        if not email_val:
            errors.append({
                'row_number': idx,
                'column_name': 'Email',
                'invalid_value': email_val,
                'error_type': 'Missing Value',
                'suggested_correction': 'Enter a valid student email address.'
            })
            row_has_error = True
        elif not EMAIL_REGEX.match(email_val):
            errors.append({
                'row_number': idx,
                'column_name': 'Email',
                'invalid_value': email_val,
                'error_type': 'Invalid Format',
                'suggested_correction': 'Email must follow standard format: username@domain.extension (e.g. user@example.com).'
            })
            row_has_error = True

        # 5. Age Validation (Type & Range 16 - 100)
        age_val = get_val('Age')
        if not age_val:
            errors.append({
                'row_number': idx,
                'column_name': 'Age',
                'invalid_value': age_val,
                'error_type': 'Missing Value',
                'suggested_correction': 'Provide the student age.'
            })
            row_has_error = True
        else:
            try:
                age_num = int(age_val)
                if age_num < 16 or age_num > 100:
                    errors.append({
                        'row_number': idx,
                        'column_name': 'Age',
                        'invalid_value': age_val,
                        'error_type': 'Out of Range',
                        'suggested_correction': 'Age must be within valid admission range between 16 and 100.'
                    })
                    row_has_error = True
            except ValueError:
                errors.append({
                    'row_number': idx,
                    'column_name': 'Age',
                    'invalid_value': age_val,
                    'error_type': 'Invalid Type',
                    'suggested_correction': 'Age must be a numeric integer value (e.g., 20).'
                })
                row_has_error = True

        # 6. Department Validation (Predefined category list)
        dept_val = get_val('Department')
        if not dept_val:
            errors.append({
                'row_number': idx,
                'column_name': 'Department',
                'invalid_value': dept_val,
                'error_type': 'Missing Value',
                'suggested_correction': f'Specify a department from: {", ".join(sorted(VALID_DEPARTMENTS))}.'
            })
            row_has_error = True
        elif dept_val.upper() not in VALID_DEPARTMENTS:
            errors.append({
                'row_number': idx,
                'column_name': 'Department',
                'invalid_value': dept_val,
                'error_type': 'Invalid Category',
                'suggested_correction': f'Department must be one of: {", ".join(sorted(VALID_DEPARTMENTS))}.'
            })
            row_has_error = True

        # 7. CGPA Validation (Type float, Range 0.00 to 10.00)
        cgpa_val = get_val('CGPA')
        if not cgpa_val:
            errors.append({
                'row_number': idx,
                'column_name': 'CGPA',
                'invalid_value': cgpa_val,
                'error_type': 'Missing Value',
                'suggested_correction': 'Provide a cumulative grade point average (CGPA).'
            })
            row_has_error = True
        else:
            try:
                cgpa_num = float(cgpa_val)
                if cgpa_num < 0.0 or cgpa_num > 10.0:
                    errors.append({
                        'row_number': idx,
                        'column_name': 'CGPA',
                        'invalid_value': cgpa_val,
                        'error_type': 'Out of Range',
                        'suggested_correction': 'CGPA must be a decimal score between 0.00 and 10.00.'
                    })
                    row_has_error = True
            except ValueError:
                errors.append({
                    'row_number': idx,
                    'column_name': 'CGPA',
                    'invalid_value': cgpa_val,
                    'error_type': 'Invalid Type',
                    'suggested_correction': 'CGPA must be a decimal floating-point number (e.g., 8.75).'
                })
                row_has_error = True

        # 8. Enrollment_Date Validation (Format YYYY-MM-DD)
        date_val = get_val('Enrollment_Date')
        if not date_val:
            errors.append({
                'row_number': idx,
                'column_name': 'Enrollment_Date',
                'invalid_value': date_val,
                'error_type': 'Missing Value',
                'suggested_correction': 'Enter an enrollment date.'
            })
            row_has_error = True
        else:
            try:
                datetime.strptime(date_val, '%Y-%m-%d')
            except ValueError:
                errors.append({
                    'row_number': idx,
                    'column_name': 'Enrollment_Date',
                    'invalid_value': date_val,
                    'error_type': 'Invalid Format',
                    'suggested_correction': 'Date must match ISO 8601 standard: YYYY-MM-DD (e.g., 2023-08-15).'
                })
                row_has_error = True

        if row_has_error:
            rows_with_errors.add(idx)

    invalid_rows = len(rows_with_errors)
    valid_rows = total_rows - invalid_rows

    return {
        'total_rows': total_rows,
        'valid_rows': valid_rows,
        'invalid_rows': invalid_rows,
        'total_errors': len(errors),
        'errors': errors
    }


# --- Web Routes ---
@app.route('/')
def landing():
    """Attractive landing page introducing DataCheck."""
    return render_template('landing.html', active_page='landing')


@app.route('/dashboard')
def dashboard():
    """Main CSV Upload and Validation Dashboard."""
    init_db()
    conn = get_db()
    try:
        recent_runs = conn.execute("""
            SELECT * FROM validation_runs 
            ORDER BY id DESC LIMIT 5
        """).fetchall()

        system_stats = conn.execute("""
            SELECT 
                COUNT(id) AS total_runs,
                COALESCE(SUM(total_rows), 0) AS total_rows_scanned,
                COALESCE(SUM(valid_rows), 0) AS total_valid_rows,
                COALESCE(SUM(total_errors), 0) AS total_errors_caught
            FROM validation_runs
        """).fetchone()
    finally:
        conn.close()

    return render_template(
        'index.html',
        active_page='dashboard',
        recent_runs=recent_runs,
        system_stats=system_stats
    )


@app.route('/index')
def index():
    """Redirect for index route."""
    return redirect(url_for('landing'))


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    """Handles CSV upload, executes validation, stores audit log in SQLite."""
    if request.method == 'GET':
        return redirect(url_for('dashboard'))

    if 'file' not in request.files:
        flash("No file part in the request.", "danger")
        return redirect(url_for('dashboard'))

    file = request.files['file']
    if file.filename == '':
        flash("No file was selected for upload.", "danger")
        return redirect(url_for('dashboard'))

    filename = secure_filename(file.filename)
    if not filename.lower().endswith('.csv'):
        flash("Unsupported file format! Please upload a valid .csv file.", "danger")
        return redirect(url_for('dashboard'))

    # Read uploaded bytes with fallback encoding support
    file_bytes = file.read()
    if len(file_bytes) == 0:
        flash("The uploaded file is empty (0 bytes).", "danger")
        return redirect(url_for('dashboard'))

    file_size_kb = round(len(file_bytes) / 1024, 2)

    # Attempt decoding with UTF-8, then fallback to Latin-1
    content_str = None
    for encoding in ['utf-8-sig', 'utf-8', 'latin-1']:
        try:
            content_str = file_bytes.decode(encoding)
            break
        except UnicodeDecodeError:
            continue

    if content_str is None:
        flash("Unable to decode the file text. Please ensure the CSV is UTF-8 encoded.", "danger")
        return redirect(url_for('dashboard'))

    # Perform Rule Validation
    result = validate_csv(content_str)
    if 'fatal_error' in result:
        flash(result['fatal_error'], "danger")
        return redirect(url_for('dashboard'))

    # Determine overall status
    status = "Clean" if result['total_errors'] == 0 else "Errors Detected"
    uploaded_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Persist summary and error records in SQLite
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO validation_runs 
        (filename, uploaded_at, file_size_kb, total_rows, valid_rows, invalid_rows, total_errors, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        filename,
        uploaded_at,
        file_size_kb,
        result['total_rows'],
        result['valid_rows'],
        result['invalid_rows'],
        result['total_errors'],
        status
    ))
    run_id = cursor.lastrowid

    # Batch insert errors for optimal performance
    if result['errors']:
        error_tuples = [
            (
                run_id,
                err['row_number'],
                err['column_name'],
                err['invalid_value'],
                err['error_type'],
                err['suggested_correction']
            )
            for err in result['errors']
        ]
        cursor.executemany("""
            INSERT INTO validation_errors 
            (run_id, row_number, column_name, invalid_value, error_type, suggested_correction)
            VALUES (?, ?, ?, ?, ?, ?)
        """, error_tuples)

    conn.commit()
    conn.close()

    flash(f"Validation completed successfully for '{filename}'.", "success")
    return redirect(url_for('view_run', run_id=run_id))


@app.route('/run/<int:run_id>')
def view_run(run_id):
    """Displays detailed validation results and error logs for a specific run."""
    conn = get_db()
    run = conn.execute("SELECT * FROM validation_runs WHERE id = ?", (run_id,)).fetchone()
    if run is None:
        conn.close()
        flash(f"Validation Run #{run_id} does not exist.", "danger")
        return redirect(url_for('history'))

    errors = conn.execute("""
        SELECT * FROM validation_errors 
        WHERE run_id = ? 
        ORDER BY row_number ASC, id ASC
    """, (run_id,)).fetchall()

    # Aggregate breakdown of errors by error_type
    error_summary = conn.execute("""
        SELECT error_type, COUNT(*) as count 
        FROM validation_errors 
        WHERE run_id = ? 
        GROUP BY error_type 
        ORDER BY count DESC
    """, (run_id,)).fetchall()

    conn.close()
    return render_template(
        'results.html',
        active_page='results',
        run=run,
        errors=errors,
        error_summary=error_summary
    )


@app.route('/history')
def history():
    """Displays list of all past validation runs."""
    conn = get_db()
    runs = conn.execute("""
        SELECT * FROM validation_runs 
        ORDER BY id DESC
    """).fetchall()
    conn.close()
    return render_template('history.html', active_page='history', runs=runs)


@app.route('/export/<int:run_id>')
def export_report(run_id):
    """Exports the validation error log as a downloadable CSV report."""
    conn = get_db()
    run = conn.execute("SELECT * FROM validation_runs WHERE id = ?", (run_id,)).fetchone()
    if run is None:
        conn.close()
        abort(404)

    errors = conn.execute("""
        SELECT row_number, column_name, invalid_value, error_type, suggested_correction 
        FROM validation_errors 
        WHERE run_id = ? 
        ORDER BY row_number ASC, id ASC
    """, (run_id,)).fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)

    # Write report header comments and columns
    writer.writerow(["DataCheck Validation Error Report"])
    writer.writerow([f"Run ID: {run['id']}", f"Source File: {run['filename']}", f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
    writer.writerow([f"Total Rows: {run['total_rows']}", f"Valid Rows: {run['valid_rows']}", f"Invalid Rows: {run['invalid_rows']}", f"Total Errors: {run['total_errors']}"])
    writer.writerow([])
    writer.writerow(["Row Number", "Column Name", "Incorrect Value", "Error Type", "Suggested Correction"])

    if errors:
        for err in errors:
            writer.writerow([
                err['row_number'],
                err['column_name'],
                err['invalid_value'] if err['invalid_value'] is not None else "",
                err['error_type'],
                err['suggested_correction']
            ])
    else:
        writer.writerow(["-", "-", "-", "Clean", "No errors detected in this dataset."])

    output.seek(0)
    export_filename = f"datacheck_report_run_{run_id}_{secure_filename(run['filename'])}"
    if not export_filename.endswith('.csv'):
        export_filename += '.csv'

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={export_filename}"}
    )


@app.route('/download-sample')
def download_sample():
    """Serves the sample dataset containing valid and intentional invalid records."""
    if not os.path.exists(SAMPLE_CSV_PATH):
        flash("Sample CSV file not found on server.", "danger")
        return redirect(url_for('index'))
    return send_file(
        SAMPLE_CSV_PATH,
        mimetype='text/csv',
        as_attachment=True,
        download_name='sample_data.csv'
    )


@app.route('/delete-run/<int:run_id>', methods=['POST'])
def delete_run(run_id):
    """Deletes a validation run and its associated errors."""
    conn = get_db()
    conn.execute("DELETE FROM validation_runs WHERE id = ?", (run_id,))
    conn.commit()
    conn.close()
    flash(f"Validation Run #{run_id} deleted successfully.", "info")
    return redirect(url_for('history'))


# --- Application Entrypoint ---
if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', '5000'))
    print(f"DataCheck Server starting on port {port}")
    app.run(debug=False, host='0.0.0.0', port=port)
