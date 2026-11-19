"""Round-four explicit metadata, public search and notice-only demo previews."""
from urllib.parse import urlencode

from server import db
from server.discovery import GENRES
from tests.support import ServerTestCase


class RoundFourTests(ServerTestCase):
    def create(self, **changes):
        return self.client('elena-voss').json('POST', '/api/opportunities', {
            'title': 'Explicit discovery test', 'deadline': '2027-06-01', **changes})

    def search(self, **filters):
        status, result = self.client('leo-marquez').json('GET', '/api/opportunities?' + urlencode(filters))
        self.assertEqual(status, 200, result)
        return result['opportunities']

    def test_unknown_is_not_inferred_from_category_level_or_description(self):
        status, result = self.create(level='student', category='jazz', description='Jazz high school clinic teacher')
        self.assertEqual(status, 201, result)
        item = result['opportunity']
        self.assertEqual((item['genre'], item['eligibility'], item['student_hub']), ('', [], False))
        for filters in ({'genre': 'Jazz'}, {'eligibility': 'high_school'}, {'student_hub': '1'}):
            self.assertNotIn(item['id'], [o['id'] for o in self.search(**filters)])

    def test_explicit_and_filters_and_owned_update(self):
        status, result = self.create(genre='Rock', eligibility=['high_school', 'college'], student_hub=True,
                                     instruments=['Guitar'], city='Austin', state='TX')
        self.assertEqual(status, 201, result)
        item = result['opportunity']
        filters = dict(genre='Rock', instrument='guitar', location='Austin', q='Explicit', eligibility='college', student_hub='1')
        self.assertIn(item['id'], [o['id'] for o in self.search(**filters)])
        self.assertNotIn(item['id'], [o['id'] for o in self.search(**{**filters, 'genre': 'Jazz'})])
        url = f"/api/opportunities/{item['id']}"
        self.assertEqual(self.client('rhonda-holloway').json('PUT', url, {'genre': 'Jazz'})[0], 403)
        status, updated = self.client('elena-voss').json('PUT', url, {'genre': 'Pop'})
        self.assertEqual(status, 200, updated)
        self.assertEqual(updated['opportunity']['genre'], 'Pop')
        self.assertEqual(updated['opportunity']['eligibility'], ['high_school', 'college'])
        self.assertEqual(self.client('elena-voss').json('PUT', url, {'blind_review': False})[0], 400)

    def test_invalid_metadata_atomic_and_all_broad_genres(self):
        before = len(self.search())
        for fields in ({'genre': 'Chamber music'}, {'eligibility': ['student']}, {'student_hub': 'maybe'},
                       {'eligibility': 'college'}, {'genre': ['Jazz']}):
            status, data = self.create(**fields)
            self.assertEqual(status, 400, data)
        self.assertEqual(len(self.search()), before)
        self.assertEqual(len(GENRES), 20)
        for genre in GENRES:
            self.assertEqual(self.create(genre=genre)[0], 201, genre)

    def test_preview_catalogue_has_no_audition_or_workflow_and_no_inference(self):
        self.assertEqual(self.client().json('GET', '/api/discovery')[0], 401)
        status, result = self.client('leo-marquez').json('GET', '/api/discovery')
        self.assertEqual(status, 200, result)
        self.assertEqual(set(p['type'] for p in result['previews']), {'clinic', 'teaching'})
        for preview in result['previews']:
            self.assertTrue(preview['demo_preview'])
            self.assertIsNone(preview['workflow_url'])
            self.assertNotIn('id', preview)
            self.assertNotIn('audition_id', preview)
            self.assertIn(preview['genre'], GENRES)
            self.assertTrue(preview['school_id'])
            self.assertIn('Demo', preview['description'])
        self.assertTrue(all(p['eligibility'] == ['high_school', 'college'] for p in result['previews'] if p['type'] == 'clinic'))
        self.assertTrue(all(p['eligibility'] == [] for p in result['previews'] if p['type'] == 'teaching'))

    def test_college_discovery_and_submission_history_still_work(self):
        colleges = [o for o in self.search(type='college_audition', student_hub='1')]
        self.assertTrue(colleges)
        college = colleges[0]
        self.assertEqual(college['eligibility'], ['high_school'])
        musician = self.client('leo-marquez')
        status, clips = musician.json('GET', '/api/musicians/leo-marquez')
        self.assertEqual(status, 200, clips)
        status, result = musician.json('POST', f"/api/auditions/{college['id']}/submissions", {'clip_id': clips['clips'][0]['id']})
        self.assertEqual(status, 201, result)
        applications = musician.json('GET', '/api/my/applications')[1]['applications']
        own = next(a for a in applications if a['audition_id'] == college['id'])
        self.assertEqual(own['opportunity']['type'], 'college_audition')
        self.assertEqual(own['opportunity']['genre'], college['genre'])
        self.assertEqual(musician.json('GET', f"/api/opportunities/{college['id']}")[0], 200)

    def test_public_musician_search_only_name_instrument_location(self):
        with db.connect(self.settings.db_path) as conn:
            conn.execute("UPDATE users SET bio='privatekeywordfortest',location='Austin, UniqueState' WHERE handle='leo-marquez'")
            conn.commit()
        public = self.client()
        status, data = public.json('GET', '/api/musicians?q=Leo')
        self.assertEqual(status, 200, data)
        self.assertTrue(any(m['handle'] == 'leo-marquez' for m in data['musicians']))
        for musician in data['musicians']:
            self.assertNotIn('email', musician)
            self.assertNotIn('password_hash', musician)
        for q in ('privatekeywordfortest', '@tutti.demo', 'UniqueState'):
            self.assertEqual(public.json('GET', '/api/musicians?' + urlencode({'q': q}))[1]['musicians'], [])
        leo = next(m for m in data['musicians'] if m['handle'] == 'leo-marquez')
        query = 'Leo ' + leo['instrument'] + ' ' + leo['location'].split(',')[0]
        self.assertTrue(public.json('GET', '/api/musicians?' + urlencode({'q': query}))[1]['musicians'])
