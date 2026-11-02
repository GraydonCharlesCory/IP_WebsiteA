"""Blind review is always on: a director never learns who an applicant is, in any status."""
import json

from tests.support import FAKE_MP4, ServerTestCase, find_opportunity, musician_identity_patterns

SCORES = {"tone": 8, "rhythm": 8, "technique": 8, "musicality": 8, "preparation": 8}


class BlindReviewTests(ServerTestCase):
    """Sofia (scored, not selected) and Adam (scored, callback) are both anonymous to Elena."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        (cls.settings.clips_dir / "aiko-nakamura-2.mp4").write_bytes(FAKE_MP4)

    def setUp(self):
        self.identity_patterns = musician_identity_patterns(self.client())
        self.elena = self.client("elena-voss")
        self.audition = find_opportunity(self.elena, "Section Seat")
        self.listing_path = f"/api/auditions/{self.audition['id']}/submissions"
        self.sofia = self.submission_id_of("sofia-lindgren", self.audition["id"])
        self.adam = self.submission_id_of("adam-reyes", self.audition["id"])

    def _assert_no_identity(self, payload):
        text = json.dumps(payload)
        for pattern in self.identity_patterns:
            self.assertIsNone(pattern.search(text), pattern.pattern)

    def test_audition_json_has_no_blind_switch(self):
        self.assertNotIn("blind_review", self.audition)

    def test_list_detail_and_audio_hide_identity(self):
        listing = self.elena.json("GET", self.listing_path)[1]
        self._assert_no_identity([s for s in listing["submissions"] if s["id"] == self.sofia])
        item = [s for s in listing["submissions"] if s["id"] == self.sofia][0]
        self.assertTrue(item["musician"]["name"].startswith("Applicant A-"))
        self.assertEqual((item["musician"]["handle"], item["musician"]["anonymous"]), (None, True))
        self.assertNotIn("identity_revealed", item)
        detail = self.elena.json("GET", f"/api/submissions/{self.sofia}")[1]
        self._assert_no_identity(detail)
        self.assertNotIn("musician_clips", detail["submission"])  # no clips (and so no video) of the applicant, ever
        self.assertNotIn("video_url", detail["submission"])
        status, body, response = self.elena.request("GET", f"/api/submissions/{self.sofia}/audio")
        self.assertEqual((status, body), (200, FAKE_MP4))
        self.assertNotIn("aiko", str(response.getheaders()))

    def test_no_video_thumbnail_or_poster_routes_exist(self):
        for suffix in ("video", "thumbnail", "thumb", "poster", "still", "photo", "avatar"):
            self.assertEqual(self.elena.request("GET", f"/api/submissions/{self.sofia}/{suffix}")[0], 404, suffix)

    def test_seeded_scored_callback_applicant_is_anonymous_too(self):
        by_id = {s["id"]: s for s in self.elena.json("GET", self.listing_path)[1]["submissions"]}
        self.assertEqual(by_id[self.adam]["status"], "callback")
        self.assertTrue(all(s["musician"]["anonymous"] for s in by_id.values()))
        self._assert_no_identity(by_id)
        self._assert_no_identity(self.elena.json("GET", f"/api/submissions/{self.adam}")[1])

    def test_shortlist_review_and_scored_callback_never_reveal(self):
        self.assertEqual(self.elena.json("PUT", f"/api/submissions/{self.sofia}/review", {"scores": SCORES, "decision": "shortlist"})[0], 200)
        self._assert_no_identity(self.elena.json("GET", f"/api/submissions/{self.sofia}")[1])
        status, data = self.elena.json("PUT", f"/api/submissions/{self.sofia}/status", {"status": "callback", "message": "Please come to the live round."})
        self.assertEqual((status, data["submission"]["status"], data["submission"]["musician"]["anonymous"]), (200, "callback", True))
        self._assert_no_identity(data)
        self.assertNotIn("musician_clips", data["submission"])
        self.assertEqual(self.elena.request("GET", f"/api/submissions/{self.sofia}/audio")[0], 200)
        status, data = self.elena.json("PUT", f"/api/submissions/{self.sofia}/status", {"status": "submitted"})
        self._assert_no_identity(data)

    def test_callback_before_scoring_is_refused(self):
        honors = find_opportunity(self.client("priya-raman"), "Honors Jazz Combo")
        jordan = self.client("jordan-wells")
        clip_id = jordan.json("GET", "/api/musicians/jordan-wells")[1]["clips"][0]["id"]
        sid = jordan.json("POST", f"/api/auditions/{honors['id']}/submissions", {"clip_id": clip_id})[1]["submission"]["id"]
        priya = self.client("priya-raman")
        status, data = priya.json("PUT", f"/api/submissions/{sid}/status", {"status": "callback", "message": "Come in"})
        self.assertEqual(status, 400)
        detail = priya.json("GET", f"/api/submissions/{sid}")[1]
        self.assertTrue(detail["submission"]["musician"]["anonymous"])
        self.assertNotIn("Jordan", json.dumps(detail))

    def test_there_is_no_reveal_button_on_the_server(self):
        status, _ = self.elena.json("POST", f"/api/submissions/{self.sofia}/reveal")
        self.assertIn(status, (404, 405))
        self._assert_no_identity(self.elena.json("GET", f"/api/submissions/{self.sofia}")[1])

    def test_blind_review_cannot_be_switched_off_by_request(self):
        for value in (False, 0, "false", None):
            status, data = self.elena.json("PUT", f"/api/auditions/{self.audition['id']}", {"blind_review": value})
            self.assertEqual(status, 400, value)
            self.assertIn("always on", data["error"])
        self._assert_no_identity(self.elena.json("GET", f"/api/submissions/{self.sofia}")[1])

    def test_label_is_stable_between_list_and_detail(self):
        item = [s for s in self.elena.json("GET", self.listing_path)[1]["submissions"] if s["id"] == self.sofia][0]
        again = self.elena.json("GET", f"/api/submissions/{self.sofia}")[1]["submission"]
        self.assertEqual(item["musician"]["name"], again["musician"]["name"])

    def test_director_messages_an_applicant_through_the_submission_and_stays_anonymous(self):
        status, data = self.elena.json("POST", "/api/conversations", {"submission_id": self.sofia, "body": "Thanks for applying."})
        self.assertIn(status, (200, 201))  # 200 when another test already opened Elena's thread with Sofia
        self.assertEqual(data["conversation"]["context"]["submission_id"], self.sofia)
        self.assertEqual(data["conversation"]["other"]["name"], f"Applicant A-{self.sofia}")
        self._assert_no_identity(data)
        sofia = self.client("sofia-lindgren")
        thread_id = data["conversation"]["id"]
        received = sofia.json("GET", f"/api/conversations/{thread_id}")[1]["messages"]
        self.assertEqual(received[-1]["body"], "Thanks for applying.")  # the musician receives it
        sofia.json("POST", f"/api/conversations/{thread_id}/messages", {"body": "Happy to play live."})
        self._assert_no_identity(self.elena.json("GET", "/api/conversations")[1])
        thread = self.elena.json("GET", f"/api/conversations/{thread_id}")[1]
        self._assert_no_identity(thread)
        self.assertEqual(thread["messages"][-1]["sender_id"], None)

    def test_conversation_a_director_starts_by_user_id_still_shows_an_anonymous_partner(self):
        sofia_id = self.client("sofia-lindgren").json("GET", "/api/me")[1]["user"]["id"]
        status, data = self.elena.json("POST", "/api/conversations", {"user_id": sofia_id, "body": "hi"})
        self.assertEqual((status, data["conversation"]["other"]["anonymous"], data["conversation"]["other"]["name"].startswith("Applicant C-")), (201, True, True))
        self._assert_no_identity(data)

    def test_director_cannot_link_someone_elses_submission(self):
        status, _ = self.client("priya-raman").json("POST", "/api/conversations", {"submission_id": self.sofia, "body": "hi"})
        self.assertEqual(status, 403)


class EveryAuditionIsBlindTests(ServerTestCase):
    def test_non_callback_applicants_are_anonymous_on_every_audition(self):
        rhonda = self.client("rhonda-holloway")
        bayview = find_opportunity(rhonda, "Lead Tenor")
        listing = rhonda.json("GET", f"/api/auditions/{bayview['id']}/submissions")[1]["submissions"]
        self.assertEqual(len(listing), 2)
        self.assertTrue(all(s["musician"]["anonymous"] and s["musician"]["name"].startswith("Applicant A-") for s in listing))
        self.assertNotIn("Leo", json.dumps(listing))
        self.assertNotIn("Dana", json.dumps(listing))
