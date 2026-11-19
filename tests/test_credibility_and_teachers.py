from tests.support import ServerTestCase


class CredibilityTests(ServerTestCase):
    def test_profile_carries_badges_and_connections(self):
        profile = self.client().json("GET", "/api/musicians/adam-reyes")[1]
        union = [b for b in profile["badges"] if b["kind"] == "union"][0]
        self.assertEqual((union["label"], union["verified_by_tutti"]), ("AFM Local 802", True))
        self.assertIn(False, [b["verified_by_tutti"] for b in profile["badges"]])
        self.assertEqual(profile["connections"][0]["author"]["handle"], "elena-voss")
        self.assertTrue(profile["connections"][0]["relationship"])
        listed = {m["handle"]: m for m in self.client().json("GET", "/api/musicians")[1]["musicians"]}
        self.assertTrue(listed["ronald-pierce"]["badges"])

    def test_who_may_endorse(self):
        text = {"text": "Wonderful player.", "relationship": "Taught her"}
        path = "/api/musicians/jordan-wells/connections"
        self.assertEqual(self.client().json("POST", path, text)[0], 401)
        for handle in ("leo-marquez", "alex-chen", "jordan-wells"):  # musicians who are not teachers (and not themselves)
            self.assertEqual(self.client(handle).json("POST", path, text)[0], 403, handle)
        for handle in ("priya-raman", "ronald-pierce"):  # a director and a teacher
            status, data = self.client(handle).json("POST", path, text)
            self.assertEqual((status, data["connection"]["author"]["handle"]), (201, handle))
        self.assertEqual(self.client("ronald-pierce").json("POST", "/api/musicians/ronald-pierce/connections", text)[0], 403)
        self.assertEqual(self.client("priya-raman").json("POST", path, {"text": " "})[0], 400)
        self.assertEqual(self.client("priya-raman").json("POST", "/api/musicians/nobody/connections", text)[0], 404)
        names = [e["author"]["handle"] for e in self.client().json("GET", "/api/musicians/jordan-wells")[1]["connections"]]
        self.assertEqual(names[:2], ["ronald-pierce", "priya-raman"])

    def test_self_claimed_badges_are_never_verified(self):
        leo = self.client("leo-marquez")
        status, data = leo.json("POST", "/api/me/badges", {"kind": "union", "label": "AFM Local 9", "verified_by_tutti": True})
        self.assertEqual((status, data["badge"]["verified_by_tutti"]), (201, False))
        self.assertEqual(leo.json("POST", "/api/me/badges", {"kind": "union", "label": "afm local 9"})[0], 409)
        self.assertEqual(leo.json("POST", "/api/me/badges", {"kind": "fan club", "label": "x"})[0], 400)
        self.assertEqual(self.client("elena-voss").json("POST", "/api/me/badges", {"kind": "union", "label": "x"})[0], 403)


class TeacherTests(ServerTestCase):
    def test_teacher_directory_and_filters(self):
        teachers = self.client().json("GET", "/api/teachers")[1]["teachers"]
        self.assertEqual({t["handle"] for t in teachers}, {"ronald-pierce", "maya-okafor"})
        ronald = [t for t in teachers if t["handle"] == "ronald-pierce"][0]
        self.assertEqual((ronald["teaching"]["rate"], "Trombone" in ronald["teaching"]["instruments"]), ("$70 per hour; first lesson free", True))
        self.assertEqual([t["handle"] for t in self.client().json("GET", "/api/teachers?instrument=cello")[1]["teachers"]], ["maya-okafor"])
        self.assertEqual([t["handle"] for t in self.client().json("GET", "/api/teachers?q=denver")[1]["teachers"]], ["ronald-pierce"])
        flagged = self.client().json("GET", "/api/musicians?teacher=1")[1]["musicians"]
        self.assertEqual({m["handle"] for m in flagged}, {"ronald-pierce", "maya-okafor"})
        self.assertEqual(self.client().json("GET", "/api/musicians?teacher=maybe")[0], 400)
        self.assertIsNone(self.client().json("GET", "/api/musicians/leo-marquez")[1]["musician"]["teaching"])


class BecomeTeacherTests(ServerTestCase):
    def test_musician_becomes_a_teacher(self):
        dana = self.client("dana-brooks")
        status, data = dana.json("PUT", "/api/me", {"is_teacher": True, "teacher_blurb": "Sax lessons", "instruments_taught": ["Saxophone"], "rate_text": "$60/hr"})
        self.assertEqual((status, data["user"]["teaching"]["rate"], data["user"]["is_teacher"]), (200, "$60/hr", True))
        self.assertIn("dana-brooks", [t["handle"] for t in self.client().json("GET", "/api/teachers?instrument=saxophone")[1]["teachers"]])
        self.assertEqual(dana.json("PUT", "/api/me", {"instruments_taught": "sax"})[0], 400)
        endorse = dana.json("POST", "/api/musicians/jordan-wells/connections", {"text": "Great ear."})
        self.assertEqual(endorse[0], 201)
