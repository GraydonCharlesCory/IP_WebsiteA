from tests.support import ServerTestCase, find_opportunity


class OpportunitySearchTests(ServerTestCase):
    def setUp(self):
        self.alex = self.client("alex-chen")

    def _titles(self, query):
        status, data = self.alex.json("GET", f"/api/opportunities?{query}")
        self.assertEqual(status, 200, data)
        return [o["title"] for o in data["opportunities"]]

    def test_listing_needs_sign_in_but_ensemble_pages_are_public(self):
        anon = self.client()
        self.assertEqual(anon.json("GET", "/api/opportunities")[0], 401)
        self.assertEqual(anon.json("GET", "/api/opportunities/1")[0], 401)
        self.assertEqual(anon.json("GET", "/api/ensembles")[0], 200)

    def test_board_mixes_auditions_and_gigs(self):
        data = self.alex.json("GET", "/api/opportunities")[1]["opportunities"]
        self.assertEqual({o["type"] for o in data}, {"audition", "gig", "grant", "residency", "college_audition", "summer_camp"})
        self.assertEqual(len(data), 15)
        self.assertEqual([o["deadline"] for o in data], sorted(o["deadline"] for o in data))

    def test_filters(self):
        self.assertEqual(len(self._titles("type=gig")), 5)
        self.assertEqual(len(self._titles("type=audition")), 6)
        self.assertEqual(set(self._titles("instrument=trombone&category=jazz&type=gig")),
                         {"Sub Needed: Friday Night Trombone", "New Year's Eve Big Band Gala", "Sunday Brunch Quartet: Rotating Chairs"})
        self.assertEqual(len(self._titles("location=denver")), 5)
        self.assertEqual(len(self._titles("location=Denver%2C%20CO&type=gig")), 3)
        self.assertEqual(len(self._titles("level=student")), 4)
        self.assertEqual(len(self._titles("paid=0")), 5)
        self.assertEqual(len(self._titles("paid=1")), 10)
        self.assertEqual(self._titles("video_round=1&type=audition&category=orchestral"), ["Violin: Section Seat, Second Violins"])
        self.assertEqual(self._titles("q=gala"), ["New Year's Eve Big Band Gala"])
        self.assertEqual(self._titles("q=bayview&paid=1"), ["Lead Tenor Saxophone: 2027 Season"])
        self.assertEqual(len(self._titles("deadline_before=2026-11-24")), 3)
        self.assertEqual(self._titles("deadline_before=2026-11-14"), ["Sub Needed: Friday Night Trombone"])

    def test_sorting_and_bad_filters(self):
        newest = self.alex.json("GET", "/api/opportunities?sort=newest")[1]["opportunities"]
        self.assertEqual(len(newest), 15)
        for query in ("sort=random", "type=party", "level=god", "paid=maybe", "deadline_before=soon", "category=pop"):
            status, data = self.alex.json("GET", f"/api/opportunities?{query}")
            self.assertEqual(status, 400, query)
            self.assertIn("error", data)

    def test_opportunity_shape(self):
        gig = find_opportunity(self.alex, "Friday Night Trombone")
        self.assertEqual((gig["type"], gig["location"], gig["paid"], gig["level"]), ("gig", "Denver, CO", True, "pro"))
        self.assertEqual(gig["gig"]["three_ms"]["musicians"]["rating"], 5)
        self.assertEqual(gig["ensemble_info"]["name"], "Mile High Jazz Collective")
        audition = find_opportunity(self.alex, "Lead Tenor")
        self.assertTrue(audition["video_round_accepted"])
        self.assertEqual(audition["callback"]["date"], "2026-12-10")
        detail = self.alex.json("GET", f"/api/opportunities/{audition['id']}")[1]["opportunity"]
        self.assertEqual(detail["my_submission"], None)

    def test_v1_audition_addresses_still_work(self):
        auditions = self.alex.json("GET", "/api/auditions")[1]["auditions"]
        self.assertEqual({a["type"] for a in auditions}, {"audition"})
        status, data = self.alex.json("GET", f"/api/auditions/{auditions[0]['id']}")
        self.assertEqual((status, data["audition"]["id"]), (200, auditions[0]["id"]))


class OpportunityWriteTests(ServerTestCase):
    def test_director_posts_gig_and_audition_with_new_fields(self):
        marcus = self.client("marcus-bell")
        body = {"type": "gig", "title": "Wedding band", "deadline": "2026-12-01", "pay_text": "$150", "paid": True, "level": "semi-pro",
                "gig": {"date": "2026-12-12", "venue": "Hotel Ballroom", "money": {"rating": 4, "note": "Good"}}}
        status, data = marcus.json("POST", "/api/opportunities", body)
        self.assertEqual(status, 201, data)
        gig = data["opportunity"]
        self.assertEqual((gig["ensemble"], gig["city"], gig["gig"]["venue"], gig["gig"]["three_ms"]["money"]["rating"]),
                         ("Mile High Jazz Collective", "Denver", "Hotel Ballroom", 4))
        self.assertEqual(marcus.json("POST", "/api/opportunities", {**body, "gig": None})[0], 400)
        self.assertEqual(marcus.json("POST", "/api/opportunities", {**body, "gig": {"date": "2026-12-12", "venue": "X", "music": {"rating": 9}}})[0], 400)
        self.assertEqual(marcus.json("POST", "/api/opportunities", {**body, "deadline": "soon"})[0], 400)
        self.assertEqual(marcus.json("PUT", f"/api/opportunities/{gig['id']}", {"type": "audition"})[0], 400)
        self.assertEqual(self.client("elena-voss").json("PUT", f"/api/opportunities/{gig['id']}", {"title": "x"})[0], 403)
        self.assertEqual(self.client("alex-chen").json("POST", "/api/opportunities", body)[0], 403)

    def test_audition_defaults_and_blind_review_cannot_be_set(self):
        elena = self.client("elena-voss")
        status, data = elena.json("POST", "/api/auditions", {"title": "Viola", "deadline": "2026-12-20", "video_round_accepted": True})
        self.assertEqual(status, 201)
        audition = data["audition"]
        self.assertEqual((audition["type"], audition["city"], "blind_review" in audition), ("audition", "Chicago", True))
        status, data = elena.json("PUT", f"/api/auditions/{audition['id']}", {"callback_date": "2027-02-01", "callback_location": "Hall"})
        self.assertEqual((status, data["audition"]["callback"]["location"]), (200, "Hall"))
        for value in (False, True):
            status, data = elena.json("PUT", f"/api/auditions/{audition['id']}", {"blind_review": value})
            self.assertEqual(status, 400)
            self.assertIn("immutable", data["error"])
        self.assertEqual(elena.json("POST", "/api/auditions", {"title": "Cello", "deadline": "2026-12-20", "blind_review": False})[0], 201)


class EnsembleTests(ServerTestCase):
    def test_public_list_and_page(self):
        anon = self.client()
        ensembles = anon.json("GET", "/api/ensembles")[1]["ensembles"]
        self.assertEqual(len(ensembles), 6)
        self.assertEqual({e["category"] for e in ensembles}, {"students", "orchestral", "jazz"})
        self.assertEqual([e["name"] for e in anon.json("GET", "/api/ensembles?category=jazz")[1]["ensembles"]],
                         ["Bayview Jazz Orchestra", "Mile High Jazz Collective"])
        self.assertEqual(len(anon.json("GET", "/api/ensembles?q=denver")[1]["ensembles"]), 2)
        self.assertEqual(anon.json("GET", "/api/ensembles?category=pop")[0], 400)
        mile_high = [e for e in ensembles if e["name"].startswith("Mile High")][0]
        page = anon.json("GET", f"/api/ensembles/{mile_high['id']}")[1]["ensemble"]
        self.assertNotIn("director", page)
        self.assertNotIn("Marcus Bell", str(page["roster"]))
        self.assertEqual(len(page["open_opportunities"]), 4)
        self.assertTrue(page["highlights"] and page["roster"] and page["founded"] and page["logo_initials"])
        self.assertNotIn("requirements", page["open_opportunities"][0])
        self.assertEqual(anon.json("GET", "/api/ensembles/999")[0], 404)

    def test_only_the_director_edits_the_page(self):
        page_id = self.client().json("GET", "/api/ensembles")[1]["ensembles"][0]["id"]
        owner = [e for e in self.client("elena-voss").json("GET", "/api/ensembles")[1]["ensembles"] if e["id"] == page_id][0]["director"]["handle"]
        self.assertEqual(self.client("alex-chen").json("PUT", f"/api/ensembles/{page_id}", {"about": "x"})[0], 403)
        self.assertEqual(self.client().json("PUT", f"/api/ensembles/{page_id}", {"about": "x"})[0], 401)
        other = "elena-voss" if owner != "elena-voss" else "marcus-bell"
        self.assertEqual(self.client(other).json("PUT", f"/api/ensembles/{page_id}", {"about": "x"})[0], 403)
        status, data = self.client(owner).json("PUT", f"/api/ensembles/{page_id}", {"about": "New about", "roster": [{"name": "A B", "instrument": "Bass"}]})
        self.assertEqual((status, data["ensemble"]["about"], data["ensemble"]["roster"][0]["name"]), (200, "New about", "A B"))
        self.assertEqual(self.client(owner).json("PUT", f"/api/ensembles/{page_id}", {"roster": ["bad"]})[0], 400)

    def test_musician_ensemble_and_gig_navigation_does_not_restore_directors(self):
        musician = self.client("leo-marquez")
        directors = self.client().json("GET", "/api/accounts")[1]["directors"]
        for ensemble in musician.json("GET", "/api/ensembles")[1]["ensembles"]:
            self.assertNotIn("director", ensemble)
            detail = musician.json("GET", f"/api/ensembles/{ensemble['id']}")[1]["ensemble"]
            self.assertNotIn("director", detail)
            for director in directors:
                self.assertNotIn(director["name"], str(detail["roster"]))
        for opportunity in musician.json("GET", "/api/opportunities")[1]["opportunities"]:
            self.assertNotIn("director", opportunity)
            detail = musician.json("GET", f"/api/opportunities/{opportunity['id']}")[1]["opportunity"]
            self.assertNotIn("director", detail)
