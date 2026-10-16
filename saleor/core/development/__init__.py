"""Development-only module. Should not be used inside production/live code paths.

This should only be used in such locations:
- `./manage.py populatedb` (development only command, requires ``uv sync --group dev``)
- pytest (`test_*.py`, `conftest.py`, `tests/**`)
- Any other development-only helpers or locations
"""
