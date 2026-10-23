"""Blind review is always on: a director learns who an applicant is only after scoring the submission and moving it to callback."""
import json

from tests.support import FAKE_MP4, ServerTestCase, find_opportunity

SOFIA_WORDS = ("Sofia", "Lindgren", "sofia-lindgren", "sofia.lindgren", "Minneapolis", "tutti.demo", "aiko-nakamura")
SCORES = {"tone": 8, "rhythm": 8, "technique": 8, "musicality": 8, "preparation": 8}


class BlindReviewTests(ServerTestCase):
    """Sofia (scored, not selected) stays anonymous to Elena; Adam (scored, callback) is the seeded revealed applicant."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        (cls.settings.clips_dir / "aiko-nakamura-2.mp4").write_bytes(FAKE_MP4)

    def setUp(self):
        self.elena = self.client("elena-voss")
        self.audition = find_opportunity(self.elena, "Section Seat")
        self.listing_path = f"/api/auditions/{self.audition['id']}/submissions"
        self.sofia = self.submission_id_of("sofia-lindgren", self.audition["id"])
        self.adam = self.submission_id_of("adam-reyes", self.audition["id"])

    def _assert_no_identity(self, payload):
        text = json.dumps(payload)
        for word in SOFIA_WORDS:
            self.assertNotIn(word, text, word)

    def test_audition_json_has_no_blind_switch(self):
        self.assertNotIn("blind_review", self.audition)

    def test_unrevealed_list_detail_and_audio_hide_identity(self):
        listing = self.elena.json("GET", self.listing_path)[1]
        self._assert_no_identity([s for s in listing["submissions"] if s["id"] == self.sofia])
        item = [s for s in listing["submissions"] if s["id"] == self.sofia][0]
        self.assertTrue(item["musician"]["name"].startswith("Applicant A-"))
        self.assertEqual((item["musician"]["handle"], item["musician"]["anonymous"], item["identity_revealed"]), (None, True, False))
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

    def test_seeded_scored_callback_is_the_only_revealed_applicant(self):
        by_id = {s["id"]: s for s in self.elena.json("GET", self.listing_path)[1]["submissions"]}
        self.assertEqual((by_id[self.adam]["musician"]["name"], by_id[self.adam]["identity_revealed"]), ("Adam Reyes", True))
        self.assertTrue(by_id[self.sofia]["musician"]["anonymous"])

    def test_shortlist_and_review_do_not_reveal_but_scored_callback_does_and_undoing_it_hides_again(self):
        self.assertEqual(self.elena.json("PUT", f"/api/submissions/{self.sofia}/review", {"scores": SCORES, "decision": "shortlist"})[0], 200)
        self._assert_no_identity(self.elena.json("GET", f"/api/submissions/{self.sofia}")[1])
        status, data = self.elena.json("PUT", f"/api/submissions/{self.sofia}/status", {"status": "callback", "message": "Please come to the live round."})
        self.assertEqual((status, data["submission"]["musician"]["name"]), (200, "Sofia Lindgren"))
        self.assertFalse(data["submission"]["musician"]["anonymous"])
        self.assertNotIn("musician_clips", data["submission"])
        self.assertEqual(self.elena.request("GET", f"/api/submissions/{self.sofia}/audio")[0], 200)  # playback stays audio only
        status, data = self.elena.json("PUT", f"/api/submissions/{self.sofia}/status", {"status": "submitted"})
        self._assert_no_identity(data)

    def test_callback_before_scoring_is_refused_and_does_not_reveal(self):
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

    def test_messaging_an_anonymous_applicant_through_the_submission_is_refused(self):
        status, data = self.elena.json("POST", "/api/conversations", {"user_id": 1, "submission_id": self.sofia, "body": "hi"})
        self.assertEqual(status, 403)
        self.assertIn("blind review", data["error"])

    def test_musician_cannot_link_their_anonymous_submission_to_a_conversation(self):
        sofia = self.client("sofia-lindgren")
        elena_id = self.elena.json("GET", "/api/me")[1]["user"]["id"]
        status, data = sofia.json("POST", "/api/conversations", {"user_id": elena_id, "submission_id": self.sofia, "body": "hi"})
        self.assertEqual(status, 403)
        self.assertIn("blind review", data["error"])
        self.assertEqual(self.elena.json("GET", "/api/conversations")[1]["conversations"], [])


class BlindLinkAfterTheFactTests(ServerTestCase):
    def test_link_made_while_revealed_is_hidden_again_if_the_callback_is_undone(self):
        elena = self.client("elena-voss")
        audition = find_opportunity(elena, "Section Seat")
        adam_sub = self.submission_id_of("adam-reyes", audition["id"])  # seeded: scored and at callback, so revealed
        elena_id = elena.json("GET", "/api/me")[1]["user"]["id"]
        adam = self.client("adam-reyes")
        status, _ = adam.json("POST", "/api/conversations", {"user_id": elena_id, "submission_id": adam_sub, "body": "Hello"})
        self.assertEqual(status, 201)
        self.assertEqual(elena.json("GET", "/api/conversations")[1]["conversations"][0]["context"]["submission_id"], adam_sub)
        elena.json("PUT", f"/api/submissions/{adam_sub}/status", {"status": "submitted"})
        context = elena.json("GET", "/api/conversations")[1]["conversations"][0]["context"]
        self.assertEqual(context, {"opportunity": None, "submission_id": None})
        self.assertEqual(adam.json("GET", "/api/conversations")[1]["conversations"][0]["context"]["submission_id"], adam_sub)
        status, data = adam.json("POST", "/api/conversations", {"user_id": elena_id, "submission_id": adam_sub})
        self.assertEqual(status, 403)
        self.assertIn("blind review", data["error"])


class EveryAuditionIsBlindTests(ServerTestCase):
    def test_non_callback_applicants_are_anonymous_on_every_audition(self):
        rhonda = self.client("rhonda-holloway")
        bayview = find_opportunity(rhonda, "Lead Tenor")
        listing = rhonda.json("GET", f"/api/auditions/{bayview['id']}/submissions")[1]["submissions"]
        self.assertEqual(len(listing), 2)
        self.assertTrue(all(s["musician"]["anonymous"] and s["musician"]["name"].startswith("Applicant A-") for s in listing))
        self.assertNotIn("Leo", json.dumps(listing))
        self.assertNotIn("Dana", json.dumps(listing))
