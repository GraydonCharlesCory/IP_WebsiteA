import json

from tests.support import ServerTestCase, find_opportunity

SCORES = {"tone": 8, "rhythm": 8, "technique": 8, "musicality": 8, "preparation": 8}


class StatusAndFeedbackTests(ServerTestCase):
    def setUp(self):
        self.rhonda = self.client("rhonda-holloway")
        self.audition = find_opportunity(self.rhonda, "Lead Tenor")
        subs = self.rhonda.json("GET", f"/api/auditions/{self.audition['id']}/submissions")[1]["submissions"]
        self.leo = [s for s in subs if s["musician"]["handle"] == "leo-marquez"][0]["id"]
        self.dana = [s for s in subs if s["musician"]["handle"] == "dana-brooks"][0]["id"]

    def _application(self, handle, audition_id):
        apps = self.client(handle).json("GET", "/api/my/applications")[1]["applications"]
        return [a for a in apps if a["audition_id"] == audition_id][0]

    def test_v1_status_names_are_accepted_as_filters(self):
        listing = lambda query: self.rhonda.json("GET", f"/api/auditions/{self.audition['id']}/submissions{query}")  # noqa: E731
        submitted = listing("?status=submitted")[1]["submissions"]
        self.assertTrue(submitted and all(s["status"] == "submitted" for s in submitted))
        self.assertEqual(listing("?status=new")[1]["submissions"], submitted)
        self.assertEqual(listing("?status=bogus")[0], 400)
        self.assertEqual(self.rhonda.json("GET", f"/api/submissions/{self.dana}")[1]["submission"]["status_label"] in
                         ("Shortlisted", "Callback", "Not selected"), True)

    def test_callback_with_message_reaches_the_musician(self):
        body = {"status": "callback", "callback_date": "2026-12-11", "callback_location": "Studio A", "message": "Bring your mute kit."}
        status, data = self.rhonda.json("PUT", f"/api/submissions/{self.leo}/status", body)
        self.assertEqual((status, data["submission"]["status"], data["submission"]["callback"]["message"]), (200, "callback", "Bring your mute kit."))
        application = self._application("leo-marquez", self.audition["id"])
        self.assertEqual((application["status"], application["status_label"]), ("callback", "Callback"))
        self.assertEqual(application["callback"], {"date": "2026-12-11", "location": "Studio A", "message": "Bring your mute kit."})
        self.assertEqual(application["opportunity"]["title"], self.audition["title"])
        self.assertEqual(application["ensemble"]["name"], "Bayview Jazz Orchestra")
        self.rhonda.json("PUT", f"/api/submissions/{self.leo}/status", {"status": "submitted"})
        self.assertIsNone(self._application("leo-marquez", self.audition["id"])["callback"])

    def test_callback_defaults_from_audition_and_needs_something(self):
        status, data = self.rhonda.json("PUT", f"/api/submissions/{self.dana}/status", {"status": "callback"})
        self.assertEqual((status, data["submission"]["callback"]["location"]), (200, "Bayview Hall, San Francisco, CA"))
        priya = self.client("priya-raman")
        honors = find_opportunity(priya, "Honors Jazz Combo")
        jordan = self.client("jordan-wells")
        _, created = jordan.json("POST", f"/api/auditions/{honors['id']}/submissions", {"clip_id": jordan.json("GET", "/api/musicians/jordan-wells")[1]["clips"][0]["id"]})
        sid = created["submission"]["id"]
        self.assertEqual(priya.json("PUT", f"/api/submissions/{sid}/status", {"status": "callback"})[0], 400)
        self.assertEqual(priya.json("PUT", f"/api/submissions/{sid}/status", {"status": "winner"})[0], 400)
        self.assertEqual(priya.json("PUT", f"/api/submissions/{sid}/status", {"status": "callback", "callback_date": "tomorrow"})[0], 400)
        self.assertEqual(priya.json("PUT", f"/api/submissions/{sid}/status", {"status": "not_selected"})[0], 200)
        self.assertEqual(self._application("jordan-wells", honors["id"])["status"], "not_selected")

    def test_only_the_posting_director_changes_status(self):
        for who, expected in (("elena-voss", 403), ("leo-marquez", 403), (None, 401)):
            self.assertEqual(self.client(who).json("PUT", f"/api/submissions/{self.leo}/status", {"status": "shortlisted"})[0], expected)

    def test_repeated_decision_does_not_undo_a_callback(self):
        self.rhonda.json("PUT", f"/api/submissions/{self.dana}/status", {"status": "callback", "message": "Come play"})
        self.rhonda.json("PUT", f"/api/submissions/{self.dana}/review", {"decision": "shortlist", "comments": "autosave"})
        self.assertEqual(self._application("dana-brooks", self.audition["id"])["status"], "callback")
        self.rhonda.json("PUT", f"/api/submissions/{self.dana}/review", {"decision": "pass"})
        self.assertEqual(self._application("dana-brooks", self.audition["id"])["status"], "not_selected")

    def test_feedback_is_hidden_until_shared_and_never_includes_private_notes(self):
        self.rhonda.json("PUT", f"/api/submissions/{self.leo}/review",
                         {"scores": SCORES, "comments": "Lovely ballad", "notes": [{"time": 5, "text": "secret timestamped note"}]})
        before = json.dumps(self.client("leo-marquez").json("GET", "/api/my/applications")[1])
        self.assertIsNone(self._application("leo-marquez", self.audition["id"])["feedback"])
        for text in ("Lovely ballad", "secret", "8.0"):
            self.assertNotIn(text, before)
        self.assertNotIn("Lovely ballad", json.dumps(self.client("leo-marquez").json("GET", "/api/my/submissions")[1]))
        status, data = self.rhonda.json("PUT", f"/api/submissions/{self.leo}/feedback", {"shared": True})
        self.assertEqual((status, data["submission"]["review"]["feedback_shared"]), (200, True))
        feedback = self._application("leo-marquez", self.audition["id"])["feedback"]
        self.assertEqual((feedback["average"], feedback["comments"], feedback["scores"]["tone"], feedback["notes"]), (8.0, "Lovely ballad", 8, None))
        self.assertNotIn("secret", json.dumps(self.client("leo-marquez").json("GET", "/api/my/applications")[1]))
        self.rhonda.json("PUT", f"/api/submissions/{self.leo}/feedback", {"shared": True, "include_notes": True})
        self.assertEqual(self._application("leo-marquez", self.audition["id"])["feedback"]["notes"][0]["text"], "secret timestamped note")
        self.rhonda.json("PUT", f"/api/submissions/{self.leo}/feedback", {"shared": False})
        self.assertIsNone(self._application("leo-marquez", self.audition["id"])["feedback"])

    def test_cannot_share_without_a_review_or_as_someone_else(self):
        priya = self.client("priya-raman")
        honors = find_opportunity(priya, "Honors Jazz Combo")
        maya = self.client("maya-okafor")
        _, created = maya.json("POST", f"/api/auditions/{honors['id']}/submissions", {"clip_id": maya.json("GET", "/api/musicians/maya-okafor")[1]["clips"][0]["id"]})
        sid = created["submission"]["id"]
        self.assertEqual(priya.json("PUT", f"/api/submissions/{sid}/feedback", {"shared": True})[0], 400)
        self.assertEqual(priya.json("PUT", f"/api/submissions/{sid}/feedback", {"shared": "maybe"})[0], 400)
        for who, expected in (("elena-voss", 403), ("maya-okafor", 403), (None, 401)):
            self.assertEqual(self.client(who).json("PUT", f"/api/submissions/{self.dana}/feedback", {"shared": True})[0], expected)

    def test_seed_scenarios_for_adam_and_sofia(self):
        lakeshore = find_opportunity(self.rhonda, "Section Seat")["id"]
        adam = self._application("adam-reyes", lakeshore)
        self.assertEqual(adam["status"], "callback")
        self.assertIn("screen", adam["callback"]["message"])
        self.assertEqual(adam["feedback"]["average"], 8.6)
        self.assertNotIn("Private", json.dumps(adam))
        sofia = self._application("sofia-lindgren", lakeshore)
        self.assertEqual((sofia["status"], sofia["feedback"]), ("not_selected", None))

    def test_applications_are_musician_only_and_private_to_each_musician(self):
        self.assertEqual(self.client().json("GET", "/api/my/applications")[0], 401)
        self.assertEqual(self.client("rhonda-holloway").json("GET", "/api/my/applications")[0], 403)
        self.assertEqual(self.client("alex-chen").json("GET", "/api/my/applications")[1]["applications"], [])
