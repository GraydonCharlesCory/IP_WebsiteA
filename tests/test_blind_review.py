import json

from tests.support import FAKE_MP4, ServerTestCase, find_opportunity

IDENTITY_WORDS = ("Adam", "Reyes", "adam-reyes", "adam.reyes", "Sofia", "Lindgren", "sofia-lindgren", "New York", "Minneapolis",
                  "aiko-nakamura", "tutti.demo", "AFM Local 802", "Brahms Violin Concerto")


class BlindReviewTests(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        (cls.settings.clips_dir / "aiko-nakamura-1.mp4").write_bytes(FAKE_MP4)

    def setUp(self):
        self.elena = self.client("elena-voss")
        self.audition = find_opportunity(self.elena, "Section Seat")
        self.listing_path = f"/api/auditions/{self.audition['id']}/submissions"

    def _assert_no_identity(self, payload):
        text = json.dumps(payload)
        for word in IDENTITY_WORDS:
            self.assertNotIn(word, text, word)

    def test_list_detail_and_video_hide_identity(self):
        self.assertTrue(self.audition["blind_review"])
        listing = self.elena.json("GET", self.listing_path)[1]
        self._assert_no_identity(listing)
        self.assertEqual(len(listing["submissions"]), 2)
        labels = {s["musician"]["name"] for s in listing["submissions"]}
        self.assertTrue(all(label.startswith("Applicant A-") for label in labels))
        first = listing["submissions"][0]
        self.assertEqual((first["musician"]["handle"], first["musician"]["anonymous"], first["identity_revealed"]), (None, True, False))
        detail = self.elena.json("GET", f"/api/submissions/{first['id']}")[1]
        self._assert_no_identity(detail)
        self.assertEqual(detail["submission"]["musician_clips"], [])
        status, body, response = self.elena.request("GET", f"/api/submissions/{first['id']}/video")
        self.assertEqual((status, body), (200, FAKE_MP4))
        self.assertNotIn("Adam", str(response.getheaders()) + str(response.getheader("Content-Disposition")))
        self.assertNotIn("aiko", str(response.getheaders()))

    def test_label_is_stable_between_list_and_detail(self):
        item = self.elena.json("GET", self.listing_path)[1]["submissions"][0]
        again = self.elena.json("GET", f"/api/submissions/{item['id']}")[1]["submission"]
        self.assertEqual(item["musician"]["name"], again["musician"]["name"])

    def test_status_change_and_review_do_not_reveal(self):
        item = self.elena.json("GET", self.listing_path)[1]["submissions"][1]
        status, data = self.elena.json("PUT", f"/api/submissions/{item['id']}/status", {"status": "shortlisted"})
        self.assertEqual(status, 200)
        self._assert_no_identity(data)
        self.assertEqual(self.elena.json("PUT", f"/api/submissions/{item['id']}/review", {"comments": "good"})[0], 200)
        self._assert_no_identity(self.elena.json("GET", self.listing_path)[1])

    def test_messaging_a_blind_applicant_through_the_submission_is_refused(self):
        item = self.elena.json("GET", self.listing_path)[1]["submissions"][0]
        status, data = self.elena.json("POST", "/api/conversations", {"user_id": 1, "submission_id": item["id"], "body": "hi"})
        self.assertEqual(status, 403)
        self.assertIn("blind review", data["error"])

    def test_musician_cannot_link_their_blind_submission_to_a_conversation(self):
        adam = self.client("adam-reyes")
        sub_id = [a for a in adam.json("GET", "/api/my/applications")[1]["applications"] if a["audition_id"] == self.audition["id"]][0]["id"]
        elena_id = self.elena.json("GET", "/api/me")[1]["user"]["id"]
        status, data = adam.json("POST", "/api/conversations", {"user_id": elena_id, "submission_id": sub_id, "body": "hi"})
        self.assertEqual(status, 403)
        self.assertIn("blind review", data["error"])
        self.assertEqual(self.elena.json("GET", "/api/conversations")[1]["conversations"], [])




class BlindLinkAfterTheFactTests(ServerTestCase):
    def test_existing_link_is_hidden_from_the_director_once_blind_is_on(self):
        elena = self.client("elena-voss")
        audition = find_opportunity(elena, "Section Seat")
        elena.json("PUT", f"/api/auditions/{audition['id']}", {"blind_review": False})
        listing = elena.json("GET", f"/api/auditions/{audition['id']}/submissions")[1]["submissions"]
        adam_sub = [s for s in listing if s["musician"]["handle"] == "adam-reyes"][0]["id"]
        elena_id = elena.json("GET", "/api/me")[1]["user"]["id"]
        adam = self.client("adam-reyes")
        status, _ = adam.json("POST", "/api/conversations", {"user_id": elena_id, "submission_id": adam_sub, "body": "Hello"})
        self.assertEqual(status, 201)
        self.assertEqual(elena.json("GET", "/api/conversations")[1]["conversations"][0]["context"]["submission_id"], adam_sub)
        elena.json("PUT", f"/api/auditions/{audition['id']}", {"blind_review": True})
        context = elena.json("GET", "/api/conversations")[1]["conversations"][0]["context"]
        self.assertEqual(context, {"opportunity": None, "submission_id": None})
        self.assertEqual(adam.json("GET", "/api/conversations")[1]["conversations"][0]["context"]["submission_id"], adam_sub)
        # while blind, Adam cannot (re)link it either
        status, data = adam.json("POST", "/api/conversations", {"user_id": elena_id, "submission_id": adam_sub})
        self.assertEqual(status, 403)
        self.assertIn("blind review", data["error"])


class BlindRevealTests(ServerTestCase):
    def setUp(self):
        self.elena = self.client("elena-voss")
        audition = find_opportunity(self.elena, "Section Seat")
        self.audition_id = audition["id"]
        self.path = f"/api/auditions/{self.audition_id}/submissions"

    def test_reveal_shows_only_that_applicant_then_blind_off_shows_everyone(self):
        items = self.elena.json("GET", self.path)[1]["submissions"]
        status, data = self.elena.json("POST", f"/api/submissions/{items[0]['id']}/reveal")
        self.assertEqual(status, 200)
        revealed = data["submission"]
        self.assertIn(revealed["musician"]["name"], ("Adam Reyes", "Sofia Lindgren"))
        self.assertFalse(revealed["musician"]["anonymous"])
        self.assertTrue(revealed["musician_clips"])
        after = self.elena.json("GET", self.path)[1]["submissions"]
        self.assertEqual(sorted(s["identity_revealed"] for s in after), [False, True])
        status, data = self.elena.json("PUT", f"/api/auditions/{self.audition_id}", {"blind_review": False})
        self.assertEqual((status, data["audition"]["blind_review"]), (200, False))
        everyone = self.elena.json("GET", self.path)[1]["submissions"]
        self.assertEqual({s["musician"]["name"] for s in everyone}, {"Adam Reyes", "Sofia Lindgren"})

    def test_non_blind_audition_shows_names(self):
        bayview = find_opportunity(self.client("rhonda-holloway"), "Lead Tenor")
        listing = self.client("rhonda-holloway").json("GET", f"/api/auditions/{bayview['id']}/submissions")[1]
        self.assertEqual({s["musician"]["name"] for s in listing["submissions"]}, {"Leo Marquez", "Dana Brooks"})
