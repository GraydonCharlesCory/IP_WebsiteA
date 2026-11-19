from urllib.parse import urlencode

from tests.support import ServerTestCase


class DescriptiveSearchTests(ServerTestCase):
    def test_genre_is_explicit_and_combines_filters(self):
        owner = self.client("elena-voss")
        status, data = owner.json("POST", "/api/opportunities", {
            "title": "Round one search fixture", "deadline": "2027-05-01",
            "description": "Baroque chamber repertoire", "instruments": ["Viola"], "genre": "Classical",
        })
        self.assertEqual(status, 201, data)
        opportunity = data["opportunity"]
        musician = self.client("leo-marquez")

        def ids(**filters):
            status, result = musician.json("GET", "/api/opportunities?" + urlencode(filters))
            self.assertEqual(status, 200, result)
            return [item["id"] for item in result["opportunities"]]

        self.assertIn(opportunity["id"], ids(genre="Classical", instrument="viola", location="Chicago", q="chamber"))
        self.assertNotIn(opportunity["id"], ids(genre="Classical", instrument="trombone"))
        self.assertNotIn(opportunity["id"], ids(genre="Classical", location="Denver"))
        self.assertNotIn(opportunity["id"], ids(genre="Jazz"))
        self.assertEqual(musician.json("GET", "/api/opportunities?genre=Baroque")[0], 400)


class PrivateApplicationMetadataTests(ServerTestCase):
    def test_search_metadata_is_available_only_in_own_application_list(self):
        musician = self.client("leo-marquez")
        status, result = musician.json("GET", "/api/my/applications")
        self.assertEqual(status, 200, result)
        self.assertTrue(result["applications"])
        for application in result["applications"]:
            opportunity = application["opportunity"]
            detail = musician.json("GET", f"/api/opportunities/{opportunity['id']}")[1]["opportunity"]
            self.assertEqual(opportunity["instruments"], detail["instruments"])
            self.assertEqual(opportunity["description"], detail["description"])
            self.assertEqual(opportunity["location"], detail["location"])
            self.assertNotIn("director", opportunity)
            self.assertNotIn("submissions", opportunity)
        for client, expected in ((self.client(), 401), (self.client("elena-voss"), 403), (self.client("lakefront-school"), 403)):
            self.assertEqual(client.json("GET", "/api/my/applications")[0], expected)
