from tests.support import ServerTestCase, find_opportunity


class MessagingTests(ServerTestCase):
    def _user_id(self, handle):
        return self.client(handle).json("GET", "/api/me")[1]["user"]["id"]

    def test_unread_badge_in_me_and_conversation_list(self):
        adam = self.client("adam-reyes")
        me = adam.json("GET", "/api/me")[1]["user"]
        self.assertEqual(me["unread_messages"], 1)
        data = adam.json("GET", "/api/conversations")[1]
        self.assertEqual(data["unread_total"], 1)
        thread = data["conversations"][0]
        self.assertEqual((thread["other"]["handle"], thread["unread_count"], thread["last_message"]["mine"]), ("naomi-castellanos", 1, False))
        self.assertIn("January 10", thread["last_message"]["body"])
        self.assertEqual(thread["context"]["opportunity"]["title"], "Violin: Section Seats and Sub List")
        self.assertEqual(self.client().json("GET", "/api/me")[1]["user"], None)

    def test_mark_read_clears_unread(self):
        alex = self.client("alex-chen")
        before = alex.json("GET", "/api/me")[1]["user"]["unread_messages"]
        self.assertEqual(before, 1)  # Ronald's reply; Alex's own message is not unread for him
        thread = [c for c in alex.json("GET", "/api/conversations")[1]["conversations"] if c["unread_count"]][0]
        status, detail = alex.json("GET", f"/api/conversations/{thread['id']}")
        self.assertEqual((status, len(detail["messages"])), (200, 2))
        self.assertEqual(alex.json("GET", "/api/me")[1]["user"]["unread_messages"], 1)  # opening does not mark read
        status, data = alex.json("POST", f"/api/conversations/{thread['id']}/read")
        self.assertEqual((status, data["unread_total"]), (200, 0))
        self.assertEqual(alex.json("GET", "/api/me")[1]["user"]["unread_messages"], 0)

    def test_send_start_and_context(self):
        jordan, priya = self.client("jordan-wells"), self.client("priya-raman")
        priya_id = self._user_id("priya-raman")
        honors = find_opportunity(jordan, "Honors Jazz Combo")
        status, data = jordan.json("POST", "/api/conversations", {"user_id": priya_id, "audition_id": honors["id"], "body": "Is the video round required?"})
        self.assertEqual(status, 201, data)
        conversation = data["conversation"]
        self.assertEqual(conversation["context"]["opportunity"]["id"], honors["id"])
        self.assertEqual(conversation["last_message"]["mine"], True)
        again = jordan.json("POST", "/api/conversations", {"user_id": priya_id, "body": "Second question"})
        self.assertEqual((again[0], again[1]["conversation"]["id"]), (200, conversation["id"]))
        self.assertEqual(priya.json("GET", "/api/conversations")[1]["conversations"][0]["unread_count"], 2)
        status, sent = priya.json("POST", f"/api/conversations/{conversation['id']}/messages", {"body": "Video is optional."})
        self.assertEqual((status, sent["message"]["mine"]), (201, True))
        self.assertEqual(jordan.json("GET", "/api/me")[1]["user"]["unread_messages"], 1)
        # newest activity first
        self.assertEqual(jordan.json("GET", "/api/conversations")[1]["conversations"][0]["id"], conversation["id"])

    def test_validation(self):
        leo = self.client("leo-marquez")
        self.assertEqual(leo.json("POST", "/api/conversations", {"user_id": self._user_id("leo-marquez")})[0], 400)
        self.assertEqual(leo.json("POST", "/api/conversations", {"user_id": 9999})[0], 404)
        self.assertEqual(leo.json("POST", "/api/conversations", {"user_id": self._user_id("dana-brooks"), "body": "  "})[0], 400)
        self.assertEqual(leo.json("POST", "/api/conversations", {"user_id": self._user_id("dana-brooks"), "audition_id": 9999})[0], 404)
        self.assertEqual(leo.json("POST", "/api/conversations", {"user_id": self._user_id("dana-brooks"), "submission_id": 9999})[0], 403)

    def test_only_participants_can_read_or_write(self):
        adam = self.client("adam-reyes")
        thread_id = adam.json("GET", "/api/conversations")[1]["conversations"][0]["id"]
        for who, expected in (("leo-marquez", 403), ("naomi-castellanos", 200), (None, 401)):
            self.assertEqual(self.client(who).json("GET", f"/api/conversations/{thread_id}")[0], expected, who)
        for who, expected in (("leo-marquez", 403), (None, 401)):
            client = self.client(who)
            self.assertEqual(client.json("POST", f"/api/conversations/{thread_id}/messages", {"body": "hi"})[0], expected)
            self.assertEqual(client.json("POST", f"/api/conversations/{thread_id}/read")[0], expected)
        self.assertEqual(adam.json("GET", "/api/conversations/99999")[0], 404)
        self.assertEqual(self.client().json("GET", "/api/conversations")[0], 401)
        outsider = self.client("leo-marquez").json("GET", "/api/conversations")[1]["conversations"]
        self.assertNotIn(thread_id, [c["id"] for c in outsider])

    def test_submission_context_is_limited_to_the_parties(self):
        rhonda = self.client("rhonda-holloway")
        audition = find_opportunity(rhonda, "Lead Tenor")
        sub = {"id": self.submission_id_of("dana-brooks", audition["id"])}
        leo_id = self._user_id("leo-marquez")
        dana_id = self._user_id("dana-brooks")
        self.assertEqual(self.client("elena-voss").json("POST", "/api/conversations", {"user_id": leo_id, "submission_id": sub["id"]})[0], 403)
        self.assertEqual(rhonda.json("POST", "/api/conversations", {"user_id": dana_id, "submission_id": sub["id"]})[0], 403)  # still anonymous
        rhonda.json("PUT", f"/api/submissions/{sub['id']}/status", {"status": "callback"})  # Dana is already scored
        status, data = rhonda.json("POST", "/api/conversations", {"user_id": dana_id, "submission_id": sub["id"], "body": "Callback details soon."})
        self.assertEqual((status, data["conversation"]["context"]["submission_id"]), (201, sub["id"]))
