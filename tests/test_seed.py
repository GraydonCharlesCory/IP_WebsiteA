import re
from pathlib import Path

from server import seed_data
from tests.support import ServerTestCase

CLIPS_README = Path(__file__).resolve().parent.parent / "my-clips" / "README.md"


class SeedTests(ServerTestCase):
    def test_seed_shape(self):
        accounts = self.client().json("GET", "/api/accounts")[1]
        self.assertEqual({m["category"] for m in accounts["musicians"]}, {"students", "orchestral", "jazz"})
        self.assertEqual({d["category"] for d in accounts["directors"]}, {"students", "orchestral", "jazz"})

    def test_clips_readme_lists_every_seed_file(self):
        text = CLIPS_README.read_text()
        for _, _, file_name, _ in seed_data.CLIPS:
            self.assertIn(f"`{file_name}`", text)

    def test_static_pages_and_fonts_served(self):
        client = self.client()
        for path in ("/", "/index.html", "/static/css/app.css", "/static/js/shell.js", "/static/fonts/inter-latin-400.woff2",
                     "/home.html", "/section.html", "/profile.html", "/audition.html", "/director.html", "/review.html"):
            self.assertEqual(client.request("GET", path)[0], 200, path)
        self.assertEqual(client.request("GET", "/static/../server/app.py")[0], 404)
