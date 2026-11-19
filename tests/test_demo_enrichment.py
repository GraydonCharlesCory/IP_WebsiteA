"""Read-only demo fallback, provenance boundaries, and populated-data activation."""
import tempfile
import unittest
from pathlib import Path

from server import db
from server.config import Settings
from server.demo_enrichment import CREDENTIALS, musician_examples, school_examples, opportunity_example
from tests.enrichment_fixture import populated_fixture, snapshot
from tests.support import ServerTestCase


class PopulatedEnrichmentTests(unittest.TestCase):
    def test_two_startups_preserve_every_row_file_and_authored_field(self):
        with tempfile.TemporaryDirectory() as folder:
            settings = Settings(data_dir=Path(folder) / 'data', clips_dir=Path(folder) / 'clips')
            populated_fixture(settings)
            with db.connect(settings.db_path) as conn:
                before = snapshot(conn)
                for row in conn.execute("SELECT * FROM users WHERE role='musician'"):
                    examples = musician_examples(row)
                    if row['handle'] == 'leo-marquez':
                        self.assertEqual(examples, {'education': [], 'certifications': []})
                    else:
                        self.assertEqual(len(examples['education']), 1)
                        self.assertEqual(len(examples['certifications']), 1)
                for school in conn.execute('SELECT * FROM schools'):
                    has_alumni = bool(conn.execute('SELECT 1 FROM alumni WHERE school_id=?', (school['id'],)).fetchone())
                    examples = school_examples(conn, school, has_alumni)
                    self.assertEqual(len(examples['posts']), 2)
                    self.assertEqual(len(examples['alumni']), 0 if has_alumni else 2)
                for row in conn.execute('SELECT * FROM auditions WHERE school_id IS NOT NULL'):
                    self.assertEqual(bool(opportunity_example(conn, row)), row['type'] != 'grant')
                self.assertEqual(snapshot(conn), before, 'Overlay reads must never write')


class DemoEnrichmentTests(ServerTestCase):
    def test_profile_examples_separate_from_real_fields_and_no_metrics(self):
        for handle in CREDENTIALS:
            status, result = self.client().json('GET', '/api/musicians/' + handle)
            self.assertEqual(status, 200)
            self.assertNotIn('stats', result)
            self.assertEqual(result['musician']['education'], [])
            self.assertEqual(result['musician']['certifications'], [])
            self.assertEqual(len(result['demo_enrichment']['education']), 1)
            self.assertEqual(len(result['demo_enrichment']['certifications']), 1)
            self.assertNotIn('verified_by_tutti', str(result['demo_enrichment']))
        self.assertNotIn('demo_enrichment', self.client('leo-marquez').json('GET', '/api/me')[1]['user'])

    def test_exact_identity_and_missing_field_checks(self):
        with db.connect(self.settings.db_path) as conn:
            original = dict(conn.execute("SELECT * FROM users WHERE handle='leo-marquez'").fetchone())
        for field, value in [('email', 'custom@example.invalid'), ('name', 'Custom person'),
                             ('role', 'director'), ('handle', 'custom-handle'),
                             ('category', 'students'), ('ensemble', 'Authored ensemble')]:
            self.assertEqual(musician_examples({**original, field: value}), {})
        self.assertEqual(musician_examples({**original, 'education': '[{"degree":"Keep"}]'})['education'], [])
        self.assertEqual(len(musician_examples({**original, 'education': '[{"degree":"Keep"}]'})['certifications']), 1)
        self.assertEqual(musician_examples({**original, 'certifications': '["Keep"]'})['certifications'], [])

    def test_school_samples_separate_and_ownership_unchanged(self):
        public = self.client()
        schools = public.json('GET', '/api/schools')[1]['schools']
        school = next(s for s in schools if s['name'] == 'Prairie Arts Academy')
        self.assertEqual(school['alumni'], [])
        self.assertEqual(len(school['demo_enrichment']['alumni']), 2)
        self.assertEqual(len(school['demo_enrichment']['posts']), 2)
        for example in school['demo_enrichment']['alumni']:
            self.assertEqual(set(example), {'name', 'detail'})
            self.assertIn('demo only', example['name'])
        url = f"/api/schools/{school['id']}"
        self.assertEqual(public.json('PUT', url, {'about': 'No'})[0], 401)
        self.assertEqual(self.client('lakefront-school').json('PUT', url, {'about': 'No'})[0], 403)
        self.assertEqual(self.client('leo-marquez').json('PUT', url, {'about': 'No'})[0], 403)
        owner = self.client('prairie-school')
        uid = self.client('leo-marquez').json('GET', '/api/me')[1]['user']['id']
        path = url + f'/alumni/{uid}'
        linked = owner.json('PUT', path)[1]['school']
        self.assertEqual(linked['demo_enrichment']['alumni'], [])
        unlinked = owner.json('DELETE', path)[1]['school']
        self.assertEqual(unlinked['alumni'], [])
        self.assertNotIn('Leo Marquez', str(unlinked))
        self.assertNotIn('leo-marquez', str(unlinked))
        self.assertEqual(owner.json('PUT', url, {'name': 'Authored school'})[1]['school']['demo_enrichment'], {})
        owner.json('PUT', url, {'name': school['name']})

    def test_opportunity_supplement_does_not_modify_workflow_or_authored_values(self):
        client = self.client('leo-marquez')
        rows = client.json('GET', '/api/opportunities?type=college_audition')[1]['opportunities']
        row = rows[0]
        url = f"/api/opportunities/{row['id']}"
        result = client.json('GET', url)[1]['opportunity']
        self.assertTrue(result.pop('demo_enrichment'))
        self.assertEqual(result, row)
        owner = self.client('lakefront-school')
        owner.json('PUT', url, {'requirements': ['Authored requirement']})
        self.assertEqual(client.json('GET', url)[1]['opportunity']['demo_enrichment'], '')
        owner.json('PUT', url, {'requirements': [], 'description': 'Authored description'})
        self.assertEqual(client.json('GET', url)[1]['opportunity']['demo_enrichment'], '')
