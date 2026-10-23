import http.client
import json

from tests.support import FAKE_MP4, ServerTestCase


class SubmitTests(ServerTestCase):
    def _jazz_audition(self, client):
        return [a for a in client.json("GET", "/api/auditions?category=jazz")[1]["auditions"]][0]["id"]

    def test_upload_small_mp4_then_director_streams_it(self):
        jordan = self.client("jordan-wells")
        priya = self.client("priya-raman")
        audition_id = priya.json("GET", "/api/auditions?mine=1")[1]["auditions"][0]["id"]
        status, data = jordan.upload(f"/api/auditions/{audition_id}/submissions?note=Hello&timestamps=%5B%7B%22time%22%3A5%2C%22label%22%3A%22Etude%22%7D%5D")
        self.assertEqual((status, data["submission"]["status"]), (201, "submitted"))
        submission_id = data["submission"]["id"]
        self.assertEqual(jordan.json("POST", f"/api/auditions/{audition_id}/submissions", {"clip_id": 1})[0], 409)
        detail = priya.json("GET", f"/api/submissions/{submission_id}")[1]["submission"]
        self.assertEqual((detail["note"], detail["timestamps"]), ("Hello", [{"time": 5, "label": "Etude"}]))
        status, body, response = priya.request("GET", f"/api/submissions/{submission_id}/audio")
        self.assertEqual((status, body), (200, FAKE_MP4))
        self.assertEqual(self.client("elena-voss").request("GET", f"/api/submissions/{submission_id}/audio")[0], 403)

    def test_upload_rejects_non_mp4_empty_and_oversize(self):
        maya = self.client("maya-okafor")
        elena = self.client("elena-voss")
        audition_id = elena.json("GET", "/api/auditions?mine=1")[1]["auditions"][0]["id"]
        path = f"/api/auditions/{audition_id}/submissions"
        self.assertEqual(maya.upload(path, FAKE_MP4, "video/quicktime")[0], 400)
        self.assertEqual(maya.upload(path, b"not a video at all, just text")[0], 400)
        self.assertEqual(maya.upload(path, b"")[0], 400)
        status, message = self._declare_oversize_upload(maya, path)
        self.assertEqual(status, 413)
        self.assertIn("MB", message)
        listing = elena.json("GET", f"/api/auditions/{audition_id}/submissions")[1]["submissions"]
        self.assertNotIn("maya-okafor", [s["musician"]["handle"] for s in listing])

    def _declare_oversize_upload(self, client, path):
        """Send only the headers of a 2 MB upload (over the 1 MB test cap) and read the refusal."""
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        conn.putrequest("POST", path)
        for name, value in (("Content-Type", "video/mp4"), ("Content-Length", str(2 * 1024 * 1024)), ("Cookie", client.cookie)):
            conn.putheader(name, value)
        conn.endheaders()
        response = conn.getresponse()
        return response.status, json.loads(response.read())["error"]

    def test_submit_with_profile_clip_and_only_musicians_may_submit(self):
        aiko = self.client("aiko-nakamura")
        elena = self.client("elena-voss")
        audition_id = elena.json("GET", "/api/auditions?mine=1")[1]["auditions"][0]["id"]
        self.assertEqual(elena.json("POST", f"/api/auditions/{audition_id}/submissions", {"clip_id": 1})[0], 403)
        clip_id = aiko.json("GET", "/api/musicians/aiko-nakamura")[1]["clips"][0]["id"]
        self.assertEqual(aiko.json("POST", f"/api/auditions/{audition_id}/submissions", {"clip_id": 1})[0], 400)
        status, data = aiko.json("POST", f"/api/auditions/{audition_id}/submissions", {"clip_id": clip_id, "note": "Hi"})
        self.assertEqual(status, 201)
        listing = elena.json("GET", f"/api/auditions/{audition_id}/submissions")[1]["submissions"]
        self.assertEqual(listing[0]["source"], "clip")

    def test_profile_clip_upload_is_public(self):
        jordan = self.client("jordan-wells")
        status, data = jordan.upload("/api/clips?title=New%20take")
        self.assertEqual(status, 201)
        url = data["clip"]["video_url"]
        self.assertEqual(self.client().request("GET", url)[1], FAKE_MP4)


class RangeTests(ServerTestCase):
    def _range(self, header, path="/media/clips/leo-marquez-2.mp4"):
        return self.client().request("GET", path, headers={"Range": header})

    def test_partial_content(self):
        status, body, response = self._range("bytes=4-11")
        self.assertEqual((status, body), (206, FAKE_MP4[4:12]))
        self.assertEqual(response.getheader("Content-Range"), f"bytes 4-11/{len(FAKE_MP4)}")
        self.assertEqual(response.getheader("Accept-Ranges"), "bytes")

    def test_open_ended_and_suffix_ranges(self):
        self.assertEqual(self._range("bytes=100-")[1], FAKE_MP4[100:])
        self.assertEqual(self._range("bytes=-10")[1], FAKE_MP4[-10:])

    def test_unsatisfiable_range_is_416(self):
        self.assertEqual(self._range(f"bytes={len(FAKE_MP4) + 5}-")[0], 416)

    def test_full_response_advertises_ranges(self):
        status, body, response = self.client().request("GET", "/media/clips/leo-marquez-2.mp4")
        self.assertEqual((status, response.getheader("Accept-Ranges")), (200, "bytes"))

    def test_authorized_submission_video_supports_range(self):
        director = self.client("rhonda-holloway")
        audition_id = director.json("GET", "/api/auditions?mine=1")[1]["auditions"][0]["id"]
        sid = director.json("GET", f"/api/auditions/{audition_id}/submissions")[1]["submissions"][0]["id"]
        status, body, _ = director.request("GET", f"/api/submissions/{sid}/audio", headers={"Range": "bytes=0-3"})
        self.assertEqual(status, 206)
