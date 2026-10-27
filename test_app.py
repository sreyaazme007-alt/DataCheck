"""
Automated Test Suite for DataCheck
==================================
Tests core validation algorithms, database operations, edge cases, landing page, and web routes.
Uses Python's built-in unittest module.
"""

import os
import io
import unittest
from app import app, init_db, get_db, validate_csv, DATABASE_PATH, SAMPLE_CSV_PATH


class DataCheckTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Ensure database tables exist before testing."""
        init_db()

    def setUp(self):
        """Configure test client."""
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_sample_csv_validation(self):
        """Test validation engine against sample_data.csv."""
        self.assertTrue(os.path.exists(SAMPLE_CSV_PATH), "sample_data.csv must exist")
        
        with open(SAMPLE_CSV_PATH, 'r', encoding='utf-8') as f:
            content = f.read()

        result = validate_csv(content)
        self.assertNotIn('fatal_error', result, f"Validation returned fatal error: {result.get('fatal_error')}")
        
        # 16 data rows in sample_data.csv
        self.assertEqual(result['total_rows'], 16)
        self.assertEqual(result['total_rows'], result['valid_rows'] + result['invalid_rows'])
        self.assertEqual(result['valid_rows'], 4)
        self.assertEqual(result['invalid_rows'], 12)
        self.assertEqual(result['total_errors'], 13)

        # Check all error categories
        error_types = [e['error_type'] for e in result['errors']]
        self.assertIn('Missing Value', error_types)
        self.assertIn('Duplicate ID', error_types)
        self.assertIn('Duplicate Record', error_types)
        self.assertIn('Invalid Type', error_types)
        self.assertIn('Invalid Format', error_types)
        self.assertIn('Out of Range', error_types)
        self.assertIn('Invalid Category', error_types)

    def test_edge_cases(self):
        """Test validation with empty, malformed, and missing header CSVs."""
        # 1. Empty content
        res_empty = validate_csv("")
        self.assertIn('fatal_error', res_empty)
        self.assertIn("empty", res_empty['fatal_error'].lower())

        # 2. Only headers, no data
        res_no_data = validate_csv("Student_ID,Full_Name,Email,Age,Department,CGPA,Enrollment_Date\n")
        self.assertIn('fatal_error', res_no_data)
        self.assertIn("zero data records", res_no_data['fatal_error'].lower())

        # 3. Missing required columns
        res_bad_headers = validate_csv("Student_ID,Full_Name\n101,John Doe")
        self.assertIn('fatal_error', res_bad_headers)
        self.assertIn("Missing required columns", res_bad_headers['fatal_error'])

        # 4. Perfectly clean dataset
        clean_csv = (
            "Student_ID,Full_Name,Email,Age,Department,CGPA,Enrollment_Date\n"
            "201,Alice Smith,alice@example.com,20,CSE,9.50,2023-08-15\n"
            "202,Bob Jones,bob@example.com,21,ECE,8.20,2023-08-15\n"
        )
        res_clean = validate_csv(clean_csv)
        self.assertEqual(res_clean['total_rows'], 2)
        self.assertEqual(res_clean['valid_rows'], 2)
        self.assertEqual(res_clean['invalid_rows'], 0)
        self.assertEqual(res_clean['total_errors'], 0)
        self.assertEqual(len(res_clean['errors']), 0)

    def test_homepage_redirects_to_dashboard(self):
        """The public root URL should open the actual CSV validation dashboard."""
        res = self.client.get('/')
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.headers.get('Location'), '/dashboard')

        dashboard_res = self.client.get('/dashboard')
        self.assertEqual(dashboard_res.status_code, 200)
        self.assertIn(b"Upload CSV File for Validation", dashboard_res.data)
        self.assertIn(b"Validate Dataset", dashboard_res.data)

    def test_dashboard_and_upload(self):
        """Test dashboard page, CSV upload processing, results, export, history, and deletion."""
        # 1. GET /dashboard (the CSV upload page)
        res_dash = self.client.get('/dashboard')
        self.assertEqual(res_dash.status_code, 200)
        self.assertIn(b"Upload CSV File for Validation", res_dash.data)
        self.assertIn(b"Validate Dataset", res_dash.data)

        # 2. GET /download-sample
        res_sample = self.client.get('/download-sample')
        self.assertEqual(res_sample.status_code, 200)
        self.assertIn(b"Student_ID,Full_Name", res_sample.data)

        # 3. POST /upload with sample_data.csv
        with open(SAMPLE_CSV_PATH, 'rb') as f:
            file_bytes = f.read()

        file_stream = io.BytesIO(file_bytes)
        try:
            data = {'file': (file_stream, 'sample_data.csv')}
            upload_res = self.client.post('/upload', data=data, content_type='multipart/form-data', follow_redirects=True)
        finally:
            file_stream.close()
            
        self.assertEqual(upload_res.status_code, 200)
        self.assertIn(b"Validation completed successfully", upload_res.data)
        self.assertIn(b"Detected Import Errors", upload_res.data)

        # 4. Verify DB has recorded the run
        conn = get_db()
        run = conn.execute("SELECT * FROM validation_runs ORDER BY id DESC LIMIT 1").fetchone()
        self.assertIsNotNone(run)
        self.assertEqual(run['filename'], 'sample_data.csv')
        run_id = run['id']

        # 5. GET /run/<id>
        view_res = self.client.get(f'/run/{run_id}')
        self.assertEqual(view_res.status_code, 200)
        self.assertIn(b"Validation Report #", view_res.data)

        # 6. GET /export/<id>
        export_res = self.client.get(f'/export/{run_id}')
        self.assertEqual(export_res.status_code, 200)
        self.assertEqual(export_res.mimetype, 'text/csv')
        self.assertIn(b"DataCheck Validation Error Report", export_res.data)
        self.assertIn(b"Row Number,Column Name", export_res.data)

        # 7. GET /history
        hist_res = self.client.get('/history')
        self.assertEqual(hist_res.status_code, 200)
        self.assertIn(b"sample_data.csv", hist_res.data)

        # 8. POST /delete-run/<id>
        del_res = self.client.post(f'/delete-run/{run_id}', follow_redirects=True)
        self.assertEqual(del_res.status_code, 200)
        self.assertIn(b"deleted successfully", del_res.data)

        # Verify deleted from DB
        deleted_run = conn.execute("SELECT * FROM validation_runs WHERE id = ?", (run_id,)).fetchone()
        self.assertIsNone(deleted_run)
        conn.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)
