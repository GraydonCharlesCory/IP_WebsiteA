"""Run the dependency-free browser helper tests with Node's installed runtime."""
import subprocess
import unittest
from pathlib import Path


class LocationSearchTests(unittest.TestCase):
    def test_geography_helper(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(['node', 'tests/location_search.cjs'], cwd=root,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
