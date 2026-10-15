from tests.support import ServerTestCase


class AuthTests(ServerTestCase):
    def test_signed_out_me_is_null(self):
        self.assertEqual(self.client().json("GET", "/api/me"), (200, {"user": None}))

    def test_sign_in_with_demo_password_then_me(self):
        client = self.client("leo-marquez")
        status, data = client.json("GET", "/api/me")
        self.assertEqual(data["user"]["name"], "Leo Marquez")
        self.assertEqual(data["user"]["role"], "musician")

    def test_wrong_password_is_401_with_hint(self):
        status, data = self.client().json("POST", "/api/sign-in", {"email": "leo.marquez@tutti.demo", "password": "nope"})
        self.assertEqual(status, 401)
        self.assertIn("demo", data["error"])

    def test_sign_in_as_role(self):
        client = self.client()
        status, data = client.json("POST", "/api/sign-in-as", {"role": "director"})
        self.assertEqual((status, data["user"]["role"]), (200, "director"))
        self.assertEqual(self.client().json("POST", "/api/sign-in-as", {"role": "x"})[0], 400)

    def test_switch_account_changes_user(self):
        client = self.client("leo-marquez")
        accounts = client.json("GET", "/api/accounts")[1]
        self.assertEqual(len(accounts["musicians"]), 9)
        self.assertEqual(len(accounts["directors"]), 6)
        director_id = accounts["directors"][0]["id"]
        client.json("POST", "/api/switch", {"user_id": director_id})
        self.assertEqual(client.json("GET", "/api/me")[1]["user"]["id"], director_id)
        self.assertEqual(client.json("POST", "/api/switch", {"user_id": 9999})[0], 404)

    def test_sign_out_clears_session(self):
        client = self.client("leo-marquez")
        client.json("POST", "/api/sign-out")
        self.assertIsNone(client.json("GET", "/api/me")[1]["user"])

    def test_bad_json_and_unknown_route(self):
        client = self.client()
        self.assertEqual(client.json("POST", "/api/sign-in", b"{oops", {"Content-Type": "application/json"})[0], 400)
        self.assertEqual(client.json("GET", "/api/nope")[0], 404)
        self.assertEqual(client.json("GET", "/api/sign-in")[0], 405)
