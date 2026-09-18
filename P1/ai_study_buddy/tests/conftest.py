"""conftest.py — shared pytest fixtures."""

import sys
import os

# Ensure the ai_study_buddy package directory is on sys.path so all modules
# can be imported without installation.
_pkg = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _pkg not in sys.path:
    sys.path.insert(0, _pkg)
