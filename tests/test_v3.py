"""V3 role boundaries, configurable judging and enriched profiles."""
import json
import sqlite3

from tests.support import ServerTestCase


class JudgingTests(ServerTestCase):
    def setUp(self):
        self.owner = self.client("elena-voss")
        self.musician = self.client("leo-marquez")
        code, data = self.owner.json("POST", "/api/opportunities", {
            "title": "V3 test round", "deadline": "2027-01-30", "blind_review": True,
            "rubric": ["sound", "interpretation"]})
        self.assertEqual(code, 201, data)
        self.aid = data["opportunity"]["id"]
        clip = self.musician.json("GET", "/api/musicians/leo-marquez")[1]["clips"][0]["id"]
        code, data = self.musician.json("POST", f"/api/auditions/{self.aid}/submissions", {
            "clip_id": clip, "note": "I am Leo Marquez", "timestamps": [{"time": 0, "label": "Leo's performance"}]})
        self.assertEqual(code, 201, data)
        self.sid = data["submission"]["id"]

    def guest(self):
        code, data = self.owner.json("POST", f"/api/auditions/{self.aid}/guests", {"label": "Panel guest"})
        self.assertEqual(code, 200, data)
        return data["guest_id"], {"X-Review-Key": data["url"].split("#")[1]}

    def test_guest_scope_scores_and_creator_only_composite(self):
        gid, headers = self.guest()
        guest = self.client()
        board = guest.json("GET", "/api/guest", headers=headers)[1]
        text = json.dumps(board)
        for hidden in ("Leo", "marquez", "composite", "average", "video_url", "email", "created", "note"):
            self.assertNotIn(hidden, text)
        self.assertEqual(board["rubric"], ["sound", "interpretation"])
        self.assertTrue(board["submissions"][0]["musician"]["anonymous"])
        path = f"/api/guest/submissions/{self.sid}/score"
        code, data = guest.json("PUT", path, {"scores": {"sound": 6, "interpretation": 8}}, headers)
        self.assertEqual((code, data["saved"]), (200, True))
        self.assertNotIn("composite", data)
        self.assertEqual(guest.json("GET", "/api/guest")[0], 403)
        self.assertEqual(guest.json("PUT", "/api/guest/submissions/99999/score", {"scores": {}}, headers)[0], 404)
        # Another link sees only its own scores, never the first guest's evaluation.
        _, other = self.guest()
        self.assertEqual(guest.json("GET", "/api/guest", headers=other)[1]["submissions"][0]["scores"], {})
        self.owner.json("PUT", f"/api/submissions/{self.sid}/review", {"scores": {"sound": 8, "interpretation": 10}, "comments": "Well shaped."})
        detail = self.owner.json("GET", f"/api/submissions/{self.sid}")[1]["submission"]
        self.assertEqual(detail["composite"], 8)
        self.assertEqual((detail["note"], detail["timestamps"], detail["created"], detail["source"]), ("", [], "", "recording"))
        self.owner.json("PUT", f"/api/submissions/{self.sid}/feedback", {"shared": True})
        apps = self.musician.json("GET", "/api/my/applications")[1]["applications"]
        feedback = next(a for a in apps if a["id"] == self.sid)["feedback"]
        self.assertEqual(feedback["comments"], "Well shaped.")
        for key in ("scores", "average", "composite"):
            self.assertNotIn(key, feedback)
        for who, code in ((None, 401), ("priya-raman", 403), ("leo-marquez", 403)):
            self.assertEqual(self.client(who).json("GET", f"/api/submissions/{self.sid}")[0], code)
        self.assertEqual(self.owner.json("DELETE", f"/api/auditions/{self.aid}/guests/{gid}")[0], 200)
        self.assertEqual(guest.json("GET", "/api/guest", headers=headers)[0], 403)
        self.assertEqual(guest.request("GET", f"/api/guest/submissions/{self.sid}/audio", headers=headers)[0], 403)

    def test_guest_rubric_validation_and_wrong_scope(self):
        _, headers = self.guest()
        for scores in ({}, {"sound": 8}, {"sound": True, "interpretation": 5}, {"sound": 11, "interpretation": 5}, {"sound": None, "interpretation": 5}):
            self.assertEqual(self.client().json("PUT", f"/api/guest/submissions/{self.sid}/score", {"scores": scores}, headers)[0], 400)
        other_sid = self.submission_id_of("adam-reyes", 2)
        for suffix in ("score", "audio"):
            method = "PUT" if suffix == "score" else "GET"
            self.assertEqual(self.client().json(method, f"/api/guest/submissions/{other_sid}/{suffix}", {"scores": {}}, headers)[0], 404)
        self.assertEqual(self.client("priya-raman").json("POST", f"/api/auditions/{self.aid}/guests", {})[0], 403)

    def test_rubric_configurable_before_applications_then_frozen(self):
        path = f"/api/auditions/{self.aid}/rubric"
        self.assertEqual(self.owner.json("PUT", path, {"rubric": ["phrasing"]})[0], 400)
        new = self.owner.json("POST", "/api/auditions", {"title": "Fresh rubric", "deadline": "2027-01-30"})[1]["audition"]["id"]
        for rubric in ([], ["x", "x"], ["Bad key"], "tone"):
            self.assertEqual(self.owner.json("PUT", f"/api/auditions/{new}/rubric", {"rubric": rubric})[0], 400)
        self.assertEqual(self.owner.json("PUT", f"/api/auditions/{new}/rubric", {"rubric": ["phrasing"]})[1]["rubric"], ["phrasing"])
        self.assertEqual(self.owner.json("PUT", f"/api/submissions/{self.sid}/review", {"scores": {"tone": 8}})[0], 400)

    def test_nonblind_chosen_once_identity_and_video_but_no_director_or_competition(self):
        code, data = self.owner.json("POST", "/api/auditions", {"title": "Named round", "deadline": "2027-01-30", "blind_review": False})
        self.assertEqual(code, 201)
        aid = data["audition"]["id"]
        code, data = self.musician.upload(f"/api/auditions/{aid}/submissions?note=Named%20note")
        sid = data["submission"]["id"]
        detail = self.owner.json("GET", f"/api/submissions/{sid}")[1]["submission"]
        self.assertEqual((detail["musician"]["name"], detail["note"]), ("Leo Marquez", "Named note"))
        self.assertEqual(self.owner.request("GET", f"/api/submissions/{sid}/audio", headers={"Range": "bytes=0-3"})[0], 206)
        self.assertEqual(self.owner.json("PUT", f"/api/auditions/{aid}", {"blind_review": True})[0], 400)
        with sqlite3.connect(str(self.settings.db_path)) as db:
            with self.assertRaisesRegex(sqlite3.IntegrityError, "immutable"):
                db.execute("UPDATE auditions SET blind_review=1 WHERE id=?", (aid,))
        for path in (f"/api/auditions/{aid}", f"/api/opportunities/{aid}", "/api/opportunities", "/api/my/applications"):
            result = self.musician.json("GET", path)[1]
            text = json.dumps(result)
            for hidden in ('"director"', "Elena Voss", "submission_count", "average", "composite"):
                self.assertNotIn(hidden, text)
        for who, expected in ((None, 401), ("elena-voss", 403), ("lakefront-school", 403)):
            self.assertEqual(self.client(who).request("GET", "/media/clips/leo-marquez-2.mp4")[0], expected)


class SchoolAndEducationTests(ServerTestCase):
    def test_school_page_and_opportunity_ownership(self):
        school = self.client("lakefront-school")
        pages = school.json("GET", "/api/schools")[1]["schools"]
        mine = next(s for s in pages if s["owned_by_me"])["id"]
        other = next(s for s in pages if not s["owned_by_me"])["id"]
        data = {"programs": ["Music degree", "Summer strings"], "activities": ["Chamber orchestra"], "about": "New program details"}
        self.assertEqual(school.json("PUT", f"/api/schools/{mine}", data)[1]["school"]["programs"], data["programs"])
        for who, expected in ((None, 401), ("leo-marquez", 403), ("elena-voss", 403), ("prairie-school", 403)):
            self.assertEqual(self.client(who).json("PUT", f"/api/schools/{mine}", data)[0], expected)
        self.assertEqual(school.json("PUT", f"/api/schools/{other}", data)[0], 403)
        musician_id = self.client("leo-marquez").json("GET", "/api/me")[1]["user"]["id"]
        path = f"/api/schools/{mine}/alumni/{musician_id}"
        self.assertEqual(school.json("PUT", path)[1]["school"]["alumni"][0]["handle"], "leo-marquez")
        self.assertEqual(self.client("prairie-school").json("DELETE", path)[0], 403)
        self.assertEqual(school.json("DELETE", path)[1]["school"]["alumni"], [])
        for kind in ("audition", "grant", "residency", "college_audition", "summer_camp"):
            body = {"title": "School " + kind, "type": kind, "deadline": "2027-02-01", "school_id": mine}
            code, result = school.json("POST", "/api/opportunities", body)
            self.assertEqual(code, 201, result)
            aid = result["opportunity"]["id"]
            self.assertEqual(school.json("PUT", f"/api/opportunities/{aid}", {"description": "Updated"})[0], 200)
            self.assertEqual(self.client("prairie-school").json("PUT", f"/api/opportunities/{aid}", {"title": "Hijack"})[0], 403)
            self.assertEqual(school.json("POST", "/api/opportunities", {**body, "school_id": other})[0], 403)

    def test_multiple_education_degrees_and_certifications(self):
        leo = self.client("leo-marquez")
        schools = leo.json("GET", "/api/schools")[1]["schools"]
        entries = [{"school_id": s["id"], "degree": degree} for s, degree in zip(schools, ["BM Performance", "MM Jazz"])]
        code, result = leo.json("PUT", "/api/me", {"education": entries, "certifications": ["Teaching certificate"], "instrument": "Tenor saxophone", "location": "Chicago, IL"})
        self.assertEqual(code, 200, result)
        profile = leo.json("GET", "/api/musicians/leo-marquez")[1]
        self.assertEqual(len(profile["musician"]["education"]), 2)
        self.assertEqual(profile["musician"]["certifications"], ["Teaching certificate"])
        self.assertIn("connections", profile)
        self.assertNotIn("endorsements", profile)
        for body in ({"education": "School"}, {"education": [{"school_id": 999, "degree": "BM"}]}, {"certifications": "Bad"}):
            self.assertIn(leo.json("PUT", "/api/me", body)[0], (400, 404))
        self.assertEqual(self.client("lakefront-school").json("PUT", "/api/me", {"education": entries})[0], 403)
