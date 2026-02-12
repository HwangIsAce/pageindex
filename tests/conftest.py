"""Pytest configuration."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ["PAGEINDEX_DATA_DIR"] = tempfile.mkdtemp(prefix="pageindex_test_")
