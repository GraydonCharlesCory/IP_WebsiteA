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
        (self.settings.clips_dir / "unsubmitted.mp4").write_bytes(FAKE_MP4)
        self.assertEqual(anon.request("GET", "/media/clips/unsubmitted.mp4")[1], FAKE_MP4)
        self.assertEqual(anon.request("GET", "/media/clips/..%2Fserver%2Fapp.py")[0], 404)

    def test_public_profile_clip_becomes_protected_only_when_used_in_blind_application(self):
        musician = self.client("leo-marquez")
        status, data = musician.upload("/api/clips?title=Public%20community%20take")
        self.assertEqual(status, 201)
        clip = data["clip"]
        url = clip["video_url"]
        for who in (None, "elena-voss", "lakefront-school", "aiko-nakamura"):
            client = self.client(who)
            self.assertEqual(client.request("GET", url)[1], FAKE_MP4)
            self.assertEqual(client.request("GET", url, headers={"Range": "bytes=0-3"})[:2], (206, FAKE_MP4[:4]))
        director = self.client("elena-voss")
        status, data = director.json("POST", "/api/auditions", {"title": "Protected source round", "deadline": "2027-05-01", "blind_review": True})
        self.assertEqual(status, 201)
        aid = data["audition"]["id"]
        self.assertEqual(musician.json("POST", f"/api/auditions/{aid}/submissions", {"clip_id": clip["id"]})[0], 201)
        for who, expected in ((None, 401), ("elena-voss", 403), ("lakefront-school", 403), ("aiko-nakamura", 403)):
            client = self.client(who)
            for headers in ({}, {"Range": "bytes=0-3"}, {"X-Review-Key": "invalid-placeholder"}):
                self.assertEqual(client.request("GET", url, headers=headers)[0], expected)
                self.assertEqual(client.request("GET", "/media/clips/leo-marquez-2.mp4", headers=headers)[0], expected)
        self.assertEqual(musician.request("GET", url)[1], FAKE_MP4)

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


class BlindMediaAliasTests(ServerTestCase):
    def test_blind_file_aliases_cannot_bypass_either_media_route(self):
        import os
        musician = self.client("leo-marquez")
        clip = musician.upload("/api/clips?title=Alias%20protected")[1]["clip"]
        director = self.client("elena-voss")
        aid = director.json("POST", "/api/auditions", {"title": "Alias round", "deadline": "2027-05-01", "blind_review": True})[1]["audition"]["id"]
        self.assertEqual(musician.json("POST", f"/api/auditions/{aid}/submissions", {"clip_id": clip["id"]})[0], 201)
        guest = director.json("POST", f"/api/auditions/{aid}/guests", {"label": "Alias guest"})[1]
        from urllib.parse import urlsplit
        key = urlsplit(guest["url"]).fragment
        # A valid guest capability still grants no access to original source bytes.
        self.assertEqual(self.client().json("GET", "/api/guest", headers={"X-Review-Key": key})[0], 200)
        sources = [(self.settings.clips_dir, "leo-marquez-2.mp4"),
                   (self.settings.profile_uploads_dir, clip["video_url"].rsplit("/", 1)[1])]
        urls = []
        for index, (directory, name) in enumerate(sources):
            source = directory / name
            for route, destination in (("clips", self.settings.clips_dir), ("uploads", self.settings.profile_uploads_dir)):
                # Exercise cross-directory aliases too, not just name normalization.
                for kind in ("symlink", "hardlink"):
                    alias = destination / f"alias-{index}-{kind}.mp4"
                    if kind == "symlink":
                        alias.symlink_to(source)
                    else:
                        os.link(source, alias)
                    urls.append(f"/media/{route}/{alias.name}")
            route = "clips" if index == 0 else "uploads"
            canonical = f"/media/{route}/{name}"
            self.assertEqual(musician.request("GET", canonical)[1], FAKE_MP4)
            upper = directory / name.upper()
            # On case-sensitive systems create a real filesystem alias, rather than skipping coverage.
            if not upper.exists():
                upper.symlink_to(source)
            urls.extend([canonical, f"/media/{route}/{name.upper()}"])
        for who, expected in ((None, 401), ("elena-voss", 403), ("lakefront-school", 403)):
            client = self.client(who)
            for url in urls:
                for method, headers in (("GET", {}), ("HEAD", {}), ("GET", {"Range": "bytes=0-3"}),
                                        ("GET", {"X-Review-Key": key}),
                                        ("HEAD", {"Range": "bytes=0-3", "X-Review-Key": key})):
                    self.assertEqual(client.request(method, url, headers=headers)[0], expected, (who, method, url))


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
        self.assertEqual(director.request("GET", f"/api/submissions/{submission_id}/audio")[0], 422)
        self.assertEqual(director.json("GET", f"/api/submissions/{submission_id}")[0], 200)

    def test_other_director_and_musicians_and_anonymous_are_refused(self):
        audition_id, submission_id = self._submission_id()
        paths = [f"/api/auditions/{audition_id}/submissions", f"/api/submissions/{submission_id}",
                 f"/api/submissions/{submission_id}/audio"]
        for who, expected in (("elena-voss", 403), ("leo-marquez", 403), (None, 401)):
            client = self.client(who)
            for path in paths:
                self.assertEqual(client.request("GET", path)[0], expected, (who, path))
            self.assertEqual(client.json("PUT", f"/api/submissions/{submission_id}/review", {"comments": "x"})[0], expected)

    def test_uploaded_submission_file_is_not_publicly_served(self):
        for path in ("/data/uploads/submissions/x.mp4", "/static/../data/tutti.db", "/media/uploads/x.mp4"):
            self.assertEqual(self.client("leo-marquez").request("GET", path)[0], 404)

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
