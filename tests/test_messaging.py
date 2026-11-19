"""One-way individual notices, announcements and templates use both local channels; no chat."""
import sqlite3
from tests.support import ServerTestCase, find_opportunity, musician_identity_patterns


class NotificationsTests(ServerTestCase):
    def setUp(self):
        self.owner = self.client("elena-voss")
        self.aid = find_opportunity(self.owner, "Section Seat")["id"]
        self.sid = self.submission_id_of("sofia-lindgren", self.aid)

    def test_no_unread_chat_metadata(self):
        self.assertNotIn("unread_messages", self.client("adam-reyes").json("GET", "/api/me")[1]["user"])
        self.assertIsNone(self.client().json("GET", "/api/me")[1]["user"])

    def test_read_send_mark_read_and_context_removed_for_every_role(self):
        for who in (None, "adam-reyes", "elena-voss", "lakefront-school"):
            for method, path in (("GET", "/api/conversations"), ("POST", "/api/conversations"),
                                 ("GET", "/api/conversations/1"), ("POST", "/api/conversations/1/messages"),
                                 ("POST", "/api/conversations/1/read")):
                self.assertEqual(self.client(who).json(method, path, {"user_id": 1, "submission_id": self.sid, "body": "Hi"})[0], 404)

    def test_bulk_announcement_both_channels_and_no_recipient_leak(self):
        self.assert_pool_delivery()

    def assert_pool_delivery(self):
        body = "Bring your own music stand for the live round."
        code, result = self.owner.json("POST", f"/api/auditions/{self.aid}/announcements", {"body": body})
        self.assertEqual((code, result["delivered"]), (200, 2))
        self.assertIn("simulated", result["email"])
        for handle in ("adam-reyes", "sofia-lindgren"):
            notices = self.client(handle).json("GET", "/api/my/notices")[1]["notices"]
            self.assertIn(body, [n["body"] for n in notices])
        self.assertNotIn(body, str(self.client("leo-marquez").json("GET", "/api/my/notices")[1]))
        outbox = self.owner.json("GET", f"/api/auditions/{self.aid}/outbox")[1]["outbox"]
        self.assertTrue(outbox)
        self.assertTrue(all(set(item) == {"body", "state"} and item["state"] == "simulated" for item in outbox))
        with sqlite3.connect(str(self.settings.db_path)) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM notices n LEFT JOIN email_outbox e ON e.notice_id=n.id WHERE e.id IS NULL").fetchone()[0], 0)

    def test_confirmation_and_rejection_templates(self):
        for template in ("confirmation", "rejection"):
            code, result = self.owner.json("POST", f"/api/submissions/{self.sid}/notification", {"template": template})
            self.assertEqual(code, 200, result)
        notices = self.client("sofia-lindgren").json("GET", "/api/my/notices")[1]["notices"]
        self.assertTrue(any("received" in n["body"] for n in notices))
        self.assertTrue(any("not been selected" in n["body"] for n in notices))
        sub = self.owner.json("GET", f"/api/submissions/{self.sid}")[1]["submission"]
        self.assertEqual((sub["status"], sub["callback"]), ("not_selected", None))

    def test_ownership_role_and_auth_enforced(self):
        for who, code in ((None, 401), ("adam-reyes", 403), ("priya-raman", 403), ("prairie-school", 403)):
            client = self.client(who)
            self.assertEqual(client.json("POST", f"/api/auditions/{self.aid}/announcements", {"body": "Hi"})[0], code)
            self.assertEqual(client.json("POST", f"/api/submissions/{self.sid}/notification", {"template": "rejection"})[0], code)
            self.assertEqual(client.json("GET", f"/api/auditions/{self.aid}/outbox")[0], code)
        self.assertEqual(self.owner.json("GET", "/api/my/notices")[0], 403)
        self.assertEqual(self.client().json("GET", "/api/my/notices")[0], 401)

    def test_validation(self):
        self.assertEqual(self.owner.json("POST", f"/api/auditions/{self.aid}/announcements", {"body": " "})[0], 400)
        self.assertEqual(self.owner.json("POST", f"/api/submissions/{self.sid}/notification", {"template": "accept"})[0], 400)

    def delivery_counts(self):
        with sqlite3.connect(str(self.settings.db_path)) as db:
            return tuple(db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                         for table in ("notices", "email_outbox"))

    def assert_anonymous(self, payload):
        for pattern in musician_identity_patterns(self.client()):
            self.assertIsNone(pattern.search(str(payload)), pattern.pattern)

    def test_individual_isolation_both_channels_then_pool_still_works(self):
        before = self.delivery_counts()
        body = "Individual rehearsal instructions <private>."
        code, result = self.owner.json("POST", f"/api/auditions/{self.aid}/notices",
                                       {"submission_id": self.sid, "body": body, "user_id": 1})
        self.assertEqual((code, result), (200, {"delivered": 1, "email": "simulated locally; no mail sent"}))
        self.assertEqual(self.delivery_counts(), tuple(n + 1 for n in before))
        self.assert_anonymous(result)
        for handle, received in (("sofia-lindgren", True), ("adam-reyes", False), ("leo-marquez", False)):
            notices = self.client(handle).json("GET", "/api/my/notices")[1]["notices"]
            self.assertEqual(body in [n["body"] for n in notices], received)
        outbox = self.owner.json("GET", f"/api/auditions/{self.aid}/outbox")[1]
        self.assert_anonymous(outbox)
        self.assertEqual([e for e in outbox["outbox"] if e["body"] == body], [{"body": body, "state": "simulated"}])
        self.assert_pool_delivery()

    def test_individual_invalid_requests_have_no_delivery_side_effects(self):
        path = f"/api/auditions/{self.aid}/notices"
        foreign = self.submission_id_of("leo-marquez", find_opportunity(self.owner, "Lead Tenor")["id"])
        invalid = [{"submission_id": value, "body": "Private instructions"}
                   for value in (None, True, "1", 1.5, [], {}, 0, -1, 10**30, 999999, foreign)]
        invalid += [{"submission_id": self.sid, "body": value} for value in (None, "", "  ", 4, [], "x" * 3001)]
        invalid += [{"user_id": 1, "body": "Not a submission"}, [], "{bad json"]
        before = self.delivery_counts()
        for data in invalid:
            with self.subTest(data=str(data)[:80]):
                code, result = self.owner.json("POST", path, data)
                self.assertEqual(code, 400, result)
                self.assert_anonymous(result)
                self.assertEqual(self.delivery_counts(), before)
        code, created = self.owner.json("POST", "/api/opportunities", {
            "title": "Another owned audition", "type": "audition", "deadline": "2027-02-01"})
        self.assertEqual(code, 201, created)
        other_aid = created["opportunity"]["id"]
        for aid, expected in ((other_aid, 400), (999999, 404)):
            code, result = self.owner.json("POST", f"/api/auditions/{aid}/notices",
                                           {"submission_id": self.sid, "body": "Wrong audition"})
            self.assertEqual(code, expected, result)
            self.assert_anonymous(result)
            self.assertEqual(self.delivery_counts(), before)

    def test_individual_auth_ownership_and_guest_denied(self):
        before = self.delivery_counts()
        for who, expected in ((None, 401), ("adam-reyes", 403), ("priya-raman", 403), ("lakefront-school", 403)):
            code, result = self.client(who).json("POST", f"/api/auditions/{self.aid}/notices",
                                                {"submission_id": self.sid, "body": "Private instructions"})
            self.assertEqual(code, expected, result)
            self.assert_anonymous(result)
        guest = self.client()
        invite = self.owner.json("POST", f"/api/auditions/{self.aid}/guests", {"label": "Guest"})[1]
        self.assertEqual(guest.json("POST", f"/api/auditions/{self.aid}/notices",
                                    {"submission_id": self.sid, "body": "Private instructions"},
                                    {"X-Review-Key": invite["url"].split("#")[1]})[0], 401)
        self.assertEqual(self.delivery_counts(), before)

    def test_school_creator_can_message_nonblind_applicant(self):
        school = self.client("lakefront-school")
        schools = school.json("GET", "/api/schools")[1]["schools"]
        mine = next(s["id"] for s in schools if s["owned_by_me"])
        code, result = school.json("POST", "/api/opportunities", {
            "title": "Individual school notice", "type": "audition", "deadline": "2027-02-01",
            "school_id": mine, "blind_review": False})
        self.assertEqual(code, 201, result)
        aid = result["opportunity"]["id"]
        musician = self.client("leo-marquez")
        clip = musician.json("GET", "/api/musicians/leo-marquez")[1]["clips"][0]["id"]
        sid = musician.json("POST", f"/api/auditions/{aid}/submissions", {"clip_id": clip})[1]["submission"]["id"]
        code, result = school.json("POST", f"/api/auditions/{aid}/notices", {"submission_id": sid, "body": "School instructions"})
        self.assertEqual((code, result["delivered"]), (200, 1))
        self.assertIn("School instructions", str(musician.json("GET", "/api/my/notices")[1]))
