from tests.support import ServerTestCase

SCORES = {"tone": 9, "rhythm": 8, "technique": 9, "musicality": 8, "preparation": 9}


class ReviewTests(ServerTestCase):
    def setUp(self):
        self.director = self.client("rhonda-holloway")
        audition_id = self.director.json("GET", "/api/auditions?mine=1")[1]["auditions"][0]["id"]
        subs = self.director.json("GET", f"/api/auditions/{audition_id}/submissions")[1]["submissions"]
        self.leo_submission = [s for s in subs if s["musician"]["handle"] == "leo-marquez"][0]["id"]

    def _save(self, body):
        return self.director.json("PUT", f"/api/submissions/{self.leo_submission}/review", body)

    def test_average_comments_notes_and_shortlist(self):
        status, data = self._save({"scores": SCORES, "comments": "Lovely sound", "notes": [{"time": 134, "text": "Great release"}], "decision": "shortlist"})
        self.assertEqual(status, 200)
        self.assertEqual(data["review"]["average"], 8.6)
        self.assertEqual(data["status"], "shortlisted")
        detail = self.director.json("GET", f"/api/submissions/{self.leo_submission}")[1]["submission"]
        self.assertEqual(detail["review"]["comments"], "Lovely sound")
        self.assertEqual(detail["review"]["notes"], [{"time": 134, "text": "Great release"}])
        self.assertEqual(detail["average"], 8.6)

    def test_partial_save_keeps_other_fields_and_recomputes(self):
        self._save({"scores": SCORES, "comments": "Keep me"})
        status, data = self._save({"scores": {"tone": 10}})
        self.assertEqual(data["review"]["comments"], "Keep me")
        self.assertEqual(data["review"]["average"], 8.8)

    def test_invalid_scores_and_decision(self):
        self.assertEqual(self._save({"scores": {"tone": 11}})[0], 400)
        self.assertEqual(self._save({"scores": {"tone": "high"}})[0], 400)
        self.assertEqual(self._save({"scores": {"volume": 5}})[0], 400)
        self.assertEqual(self._save({"decision": "maybe"})[0], 400)
        self.assertEqual(self._save({"notes": [{"nope": 1}]})[0], 400)

    def test_dashboard_kpis(self):
        data = self.director.json("GET", "/api/director/dashboard")[1]
        self.assertEqual(data["kpis"]["open_auditions"], 1)
        self.assertEqual(data["kpis"]["total_submissions"], 2)
        self.assertGreaterEqual(data["kpis"]["new_submissions"], 0)
        self.assertEqual(data["auditions"][0]["submission_count"], 2)
        self.assertEqual(self.client("leo-marquez").json("GET", "/api/director/dashboard")[0], 403)
