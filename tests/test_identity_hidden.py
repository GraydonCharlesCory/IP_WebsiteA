"""No director, in any submission status, can learn an applicant's identity from any audition, submission,
conversation, dashboard or media response. Public musician profiles/feeds, public ensemble pages (a roster may name
a regular sub), the demo account switcher and a gig's sub list are not audition applicant channels and are not walked here."""
import json

from tests.support import DIRECTOR_HANDLES, ServerTestCase, musician_identity_patterns

SCORES = {"tone": 7, "rhythm": 7, "technique": 7, "musicality": 7, "preparation": 7}
STATUSES = ("submitted", "shortlisted", "callback", "not_selected")


class IdentityHiddenFromDirectorsTests(ServerTestCase):
    def setUp(self):
        self.patterns = musician_identity_patterns(self.client())
        self.directors = {handle: self.client(handle) for handle in DIRECTOR_HANDLES}
        self.audited = []

    def assert_clean(self, label, status, body):
        self.audited.append(label)
        text = body.decode("utf-8", "replace") if isinstance(body, bytes) else json.dumps(body)
        for pattern in self.patterns:
            self.assertIsNone(pattern.search(text), f"{label} ({status}) leaks {pattern.pattern!r}")

    def get(self, handle, path):
        status, body, response = self.directors[handle].request("GET", path)
        self.assert_clean(f"{handle} GET {path}", status, body)
        self.assert_clean(f"{handle} GET {path} headers", status, str(response.getheaders()))
        return status, (json.loads(body) if response.getheader("Content-Type", "").startswith("application/json") else body)

    def walk_director(self, handle):
        director = self.directors[handle]
        for path in ("/api/me", "/api/director/dashboard", "/api/opportunities", "/api/auditions", "/api/conversations"):
            self.get(handle, path)
        for opp in self.get(handle, "/api/opportunities")[1]["opportunities"]:
            self.get(handle, f"/api/opportunities/{opp['id']}")
            self.get(handle, f"/api/auditions/{opp['id']}")
            if opp["type"] == "audition":
                listing = self.get(handle, f"/api/auditions/{opp['id']}/submissions")
                for item in listing[1].get("submissions", []):
                    self.get(handle, f"/api/submissions/{item['id']}")
                    self.get(handle, f"/api/submissions/{item['id']}/audio")
        for conversation in self.get(handle, "/api/conversations")[1]["conversations"]:
            self.get(handle, f"/api/conversations/{conversation['id']}")
        return director

    def test_every_director_sees_no_identity_in_the_seeded_data(self):
        for handle in DIRECTOR_HANDLES:
            self.walk_director(handle)
        self.assertTrue(any("/submissions" in label for label in self.audited))
        self.assertTrue(any("/api/conversations/" in label for label in self.audited))

    def test_no_status_change_or_feedback_reveals_anyone(self):
        for handle, director in self.directors.items():
            for opp in director.json("GET", "/api/director/dashboard")[1]["auditions"]:
                for item in director.json("GET", f"/api/auditions/{opp['id']}/submissions")[1]["submissions"]:
                    sid = item["id"]
                    self.assert_clean("review", *director.json("PUT", f"/api/submissions/{sid}/review", {"scores": SCORES, "decision": "shortlist"}))
                    for status in STATUSES:
                        code, body = director.json("PUT", f"/api/submissions/{sid}/status", {"status": status, "message": "Please come in."})
                        self.assert_clean(f"{handle} status {status}", code, body)
                        self.assertTrue(body["submission"]["musician"]["anonymous"], status)
                    self.assert_clean("feedback", *director.json("PUT", f"/api/submissions/{sid}/feedback", {"shared": True}))
        for handle in DIRECTOR_HANDLES:
            self.walk_director(handle)

    def test_conversations_with_applicants_stay_anonymous_for_the_director(self):
        elena = self.directors["elena-voss"]
        audition = [o for o in elena.json("GET", "/api/director/dashboard")[1]["auditions"] if o["submission_count"]][0]
        for item in elena.json("GET", f"/api/auditions/{audition['id']}/submissions")[1]["submissions"]:
            self.assert_clean("start", *elena.json("POST", "/api/conversations", {"submission_id": item["id"], "body": "Hello from the panel."}))
        for handle in ("adam-reyes", "sofia-lindgren"):
            musician = self.client(handle)
            for conversation in musician.json("GET", "/api/conversations")[1]["conversations"]:
                musician.json("POST", f"/api/conversations/{conversation['id']}/messages", {"body": "Thank you!"})
        listing = elena.json("GET", "/api/conversations")[1]["conversations"]
        self.assertGreaterEqual(len(listing), 2)
        for conversation in listing:
            self.assertTrue(conversation["other"]["anonymous"])
            self.assertIsNone(conversation["other"]["id"])
        self.walk_director("elena-voss")

    def test_seeded_director_threads_show_an_anonymous_partner(self):
        naomi = self.directors["naomi-castellanos"]
        thread = naomi.json("GET", "/api/conversations")[1]["conversations"][0]
        self.assertEqual((thread["other"]["anonymous"], thread["other"]["handle"], thread["other"]["id"]), (True, None, None))
        self.assertTrue(thread["other"]["name"].startswith("Applicant "))
