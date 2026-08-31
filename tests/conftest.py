"""Shared pytest configuration."""

import os

# Avoid SQLite contention from HTTP audit middleware during the test suite.
os.environ.setdefault("ALPILAB_AUDIT_HTTP", "0")
