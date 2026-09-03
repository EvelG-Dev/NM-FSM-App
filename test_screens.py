import unittest
import sqlite3
from app import app, db, Students

class StudentAppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self._cleanup_test_data()

    def tearDown(self):
        self._cleanup_test_data()

    def _cleanup_test_data(self):
        with self.app.app_context():
            test_students = Students.query.filter(Students.name.like('%Integration Test%')).all()
            for s in test_students:
                db.session.delete(s)
            db.session.commit()

    def test_database_schema_and_preserved_records(self):
        """Verify that the database has the phone column and all existing students have a phone number."""
        con = sqlite3.connect('instance/students.sqlite3')
        cur = con.cursor()
        columns = [col[1] for col in cur.execute('PRAGMA table_info(students)').fetchall()]
        self.assertIn('phone', columns, "Column 'phone' must be present in students table")

        rows = cur.execute('SELECT student_id, name, phone FROM students').fetchall()
        self.assertGreater(len(rows), 0, "There should be existing student records")
        for sid, name, phone in rows:
            self.assertIsNotNone(phone, f"Student {sid} ({name}) must have a phone number")
            self.assertTrue(len(phone) > 0, f"Student {sid} ({name}) phone number must not be empty")
            print(f"Verified student {sid}: {name} -> {phone}")
        con.close()

    def test_show_all_screen(self):
        """Verify GET / (All Students screen) renders the Phone header and student phone data."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        # Check table header contains Phone
        self.assertIn('<th>Phone</th>', html, "Table header should contain <th>Phone</th>")

        # Check FIU User ID is rendered at the top
        self.assertIn('egonz740', html, "Screen must contain FIU User ID 'egonz740'")
        self.assertIn('User ID:', html, "Screen must contain 'User ID:' label")

        # Check that existing student phone numbers are displayed
        with self.app.app_context():
            students = Students.query.all()
            for s in students:
                self.assertIn(s.phone, html, f"Phone {s.phone} for student {s.name} should appear on screen")
        print("Screen GET / verified successfully.")

    def test_new_student_screen(self):
        """Verify GET /new (Add New Student screen) renders the Phone input field and User ID."""
        response = self.client.get('/new')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        # Check FIU User ID is rendered at the top
        self.assertIn('egonz740', html, "Screen must contain FIU User ID 'egonz740'")
        self.assertIn('User ID:', html, "Screen must contain 'User ID:' label")

        # Check form contains phone field
        self.assertIn('name="phone"', html, "Form must contain input with name='phone'")
        self.assertIn('Phone:', html, "Form must contain label 'Phone:'")
        print("Screen GET /new verified successfully.")

    def test_add_student_flow(self):
        """Verify POST /new adds a new student with phone number and redirects to show_all screen."""
        new_data = {
            'name': 'Integration Test Student',
            'city': 'Tampa',
            'addr': '4200 E Fowler Ave',
            'pin': '33620',
            'phone': '813-555-0199'
        }

        # Submit new student
        response = self.client.post('/new', data=new_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        # Verify new record appears on the show_all screen
        self.assertIn('Integration Test Student', html)
        self.assertIn('813-555-0199', html)

        # Verify in database
        with self.app.app_context():
            added = Students.query.filter_by(name='Integration Test Student').first()
            self.assertIsNotNone(added)
            self.assertEqual(added.phone, '813-555-0199')
            print(f"Added and verified student {added.id}: {added.name} with phone {added.phone}")

if __name__ == '__main__':
    unittest.main()
