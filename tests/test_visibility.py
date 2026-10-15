from tests.support import FAKE_MP4, ServerTestCase


class PublicAndSignedInTests(ServerTestCase):
    def test_profiles_clips_and_posts_are_public(self):
        anon = self.client()
        status, data = anon.json("GET", "/api/musicians/leo-marquez")
        self.assertEqual(status, 200)
        self.assertEqual(len(data["clips"]), 3)
        self.assertTrue(data["posts"])
        self.assertEqual(anon.json("GET", "/api/clips")[0], 200)
        self.assertEqual(anon.json("GET", "/api/feed")[0], 200)
        self.assertEqual(anon.json("GET", "/api/sections/jazz")[0], 200)
        self.assertNotIn("email", data["musician"])

    def test_clip_availability_flag(self):
        clips = self.client().json("GET", "/api/musicians/leo-marquez")[1]["clips"]
        flags = {c["title"]: c["available"] for c in clips}
        self.assertTrue(flags["Body and Soul (ballad)"])
        self.assertFalse(flags["Oleo: trio, live at The Lantern"])

    def test_missing_library_clip_is_friendly_404_and_present_one_streams(self):
        anon = self.client()
        status, data = anon.json("GET", "/media/clips/leo-marquez-3.mp4")
        self.assertEqual(status, 404)
        self.assertIn("coming soon", data["error"])
        self.assertEqual(anon.request("GET", "/media/clips/leo-marquez-2.mp4")[0], 200)
        self.assertEqual(anon.request("GET", "/media/clips/..%2Fserver%2Fapp.py")[0], 404)

    def test_auditions_need_sign_in(self):
        self.assertEqual(self.client().json("GET", "/api/auditions")[0], 401)
        self.assertIsNone(self.client().json("GET", "/api/sections/jazz")[1]["auditions"])
        self.assertEqual(len(self.client("leo-marquez").json("GET", "/api/auditions")[1]["auditions"]), 6)

    def test_only_directors_write_auditions(self):
        body = {"title": "Bass", "ensemble": "X", "category": "jazz", "deadline": "2026-11-30"}
        self.assertEqual(self.client("leo-marquez").json("POST", "/api/auditions", body)[0], 403)
        self.assertEqual(self.client().json("POST", "/api/auditions", body)[0], 401)
        status, data = self.client("rhonda-holloway").json("POST", "/api/auditions", {**body, "requirements": ["One tune"]})
        self.assertEqual(status, 201)
        self.assertEqual(data["audition"]["requirements"], ["One tune"])

    def test_director_edits_only_own_audition(self):
        mine = self.client("priya-raman")
        audition_id = [a for a in mine.json("GET", "/api/auditions?mine=1")[1]["auditions"]][0]["id"]
        self.assertEqual(self.client("elena-voss").json("PUT", f"/api/auditions/{audition_id}", {"title": "Hijack"})[0], 403)
        status, data = mine.json("PUT", f"/api/auditions/{audition_id}", {"deadline": "2026-11-28"})
        self.assertEqual((status, data["audition"]["deadline"]), (200, "2026-11-28"))
        self.assertEqual(data["audition"]["requirements"][0], "One tune in a style you love")


class SubmissionPrivacyTests(ServerTestCase):
    def _submission_id(self):
        director = self.client("rhonda-holloway")
        audition_id = director.json("GET", "/api/auditions?mine=1")[1]["auditions"][0]["id"]
        return audition_id, director.json("GET", f"/api/auditions/{audition_id}/submissions")[1]["submissions"][0]["id"]

    def test_owner_sees_submissions_and_video(self):
        audition_id, submission_id = self._submission_id()
        director = self.client("rhonda-holloway")
        status, data = director.json("GET", f"/api/auditions/{audition_id}/submissions")
        self.assertEqual((status, len(data["submissions"])), (200, 2))
        self.assertEqual(director.request("GET", f"/api/submissions/{submission_id}/video")[0], 200)
        self.assertEqual(director.json("GET", f"/api/submissions/{submission_id}")[0], 200)

    def test_other_director_and_musicians_and_anonymous_are_refused(self):
        audition_id, submission_id = self._submission_id()
        paths = [f"/api/auditions/{audition_id}/submissions", f"/api/submissions/{submission_id}",
                 f"/api/submissions/{submission_id}/video"]
        for who, expected in (("elena-voss", 403), ("leo-marquez", 403), (None, 401)):
            client = self.client(who)
            for path in paths:
                self.assertEqual(client.request("GET", path)[0], expected, (who, path))
            self.assertEqual(client.json("PUT", f"/api/submissions/{submission_id}/review", {"comments": "x"})[0], expected)

    def test_uploaded_submission_file_is_not_publicly_served(self):
        for path in ("/data/uploads/submissions/x.mp4", "/static/../data/tutti.db", "/media/uploads/x.mp4"):
            self.assertEqual(self.client().request("GET", path)[0], 404)

    def test_musician_sees_status_but_never_unshared_scores(self):
        dana = self.client("dana-brooks")  # seeded submission carries a score and a comment
        status, data = dana.json("GET", "/api/my/submissions")
        self.assertEqual(data["submissions"][0]["status"], "shortlisted")
        self.assertNotIn("review", str(data).lower())
        audition_id = data["submissions"][0]["audition_id"]
        detail = dana.json("GET", f"/api/auditions/{audition_id}")[1]["audition"]
        self.assertEqual(detail["my_submission"]["status"], "shortlisted")
        self.assertNotIn("average", str(detail))
        self.assertNotIn("Fast, clean", str(detail) + str(data))
