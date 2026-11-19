from tests.support import ServerTestCase, find_opportunity


class GigAvailabilityTests(ServerTestCase):
    def setUp(self):
        self.marcus = self.client("marcus-bell")
        self.friday = find_opportunity(self.marcus, "Friday Night Trombone")["id"]
        self.nye = find_opportunity(self.marcus, "New Year")["id"]

    def test_musician_marks_availability_and_sees_their_own_mark(self):
        alex = self.client("alex-chen")
        status, data = alex.json("PUT", f"/api/gigs/{self.friday}/availability", {"status": "available"})
        self.assertEqual((status, data["availability"]["status"]), (200, "available"))
        self.assertEqual(alex.json("GET", f"/api/opportunities/{self.friday}")[1]["opportunity"]["my_availability"], "available")
        alex.json("PUT", f"/api/gigs/{self.friday}/availability", {"status": "maybe"})
        self.assertEqual(alex.json("GET", f"/api/opportunities/{self.friday}")[1]["opportunity"]["my_availability"], "maybe")
        self.assertEqual(alex.json("PUT", f"/api/gigs/{self.friday}/availability", {"status": "soon"})[0], 400)

    def test_sub_list_is_for_the_posting_director_only(self):
        data = self.marcus.json("GET", f"/api/gigs/{self.nye}/availability")[1]
        self.assertEqual({m["handle"] for m in data["available"]}, {"ronald-pierce", "leo-marquez", "dana-brooks"})
        self.assertEqual([m["handle"] for m in data["maybe"]], ["alex-chen"])
        self.assertEqual(data["unavailable"], [])
        self.assertEqual(self.marcus.json("GET", f"/api/opportunities/{self.nye}")[1]["opportunity"]["available_count"], 3)
        for who, expected in (("elena-voss", 403), ("ronald-pierce", 403), (None, 401)):
            self.assertEqual(self.client(who).json("GET", f"/api/gigs/{self.nye}/availability")[0], expected)

    def test_directors_cannot_mark_and_auditions_have_no_availability(self):
        self.assertEqual(self.client("elena-voss").json("PUT", f"/api/gigs/{self.nye}/availability", {"status": "available"})[0], 403)
        self.assertEqual(self.client().json("PUT", f"/api/gigs/{self.nye}/availability", {"status": "available"})[0], 401)
        audition = find_opportunity(self.marcus, "Trombone Chair")
        self.assertEqual(audition["type"], "audition")
        self.assertEqual(self.client("ronald-pierce").json("PUT", f"/api/gigs/{audition['id']}/availability", {"status": "available"})[0], 400)
        self.assertEqual(self.marcus.json("GET", f"/api/gigs/{audition['id']}/availability")[0], 400)

    def test_gigs_do_not_take_submissions(self):
        ronald = self.client("ronald-pierce")
        status, data = ronald.json("POST", f"/api/auditions/{self.friday}/submissions", {"clip_id": 1})
        self.assertEqual(status, 409)
        self.assertIn("availability", data["error"])
