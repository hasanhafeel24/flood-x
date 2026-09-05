"""
conftest.py — FLOOD-X pytest configuration
"""
import sys
from pathlib import Path

# Make backend importable from tests/
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
