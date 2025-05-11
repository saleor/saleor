import pytest
from graphql.error import GraphQLError

from ..svg_sanititzer import sanitize_svg

# Malicious SVG with a <script> tag
MALICIOUS_SVG_SCRIPT = b"""
<svg xmlns="http://www.w3.org/2000/svg">
  <script>alert("XSS")</script>
  <circle cx="50" cy="50" r="40" />
</svg>
"""

# Malicious SVG with inline onload attribute
MALICIOUS_SVG_ONLOAD = b"""
<svg xmlns="http://www.w3.org/2000/svg" onload="alert('XSS')">
  <rect width="100" height="100" />
</svg>
"""

# Safe SVG
SAFE_SVG = b"""
<svg xmlns="http://www.w3.org/2000/svg">
  <circle cx="50" cy="50" r="40" />
</svg>
"""

# Not SVG
NOT_SVG = b"hello world, this is not an SVG"


def test_sanitize_svg_removes_script_tag():
    sanitized = sanitize_svg(MALICIOUS_SVG_SCRIPT)
    assert b"<script>" not in sanitized
    assert b"alert" not in sanitized
    assert b"<circle" in sanitized


def test_sanitize_svg_removes_inline_event():
    sanitized = sanitize_svg(MALICIOUS_SVG_ONLOAD)
    assert b"onload" not in sanitized
    assert b"<rect" in sanitized


def test_sanitize_svg_preserves_safe_svg():
    sanitized = sanitize_svg(SAFE_SVG)
    assert b"<circle" in sanitized
    assert b"<script" not in sanitized


def test_sanitize_svg_invalid_input_raises():
    with pytest.raises(GraphQLError, match="SVG sanitization failed."):
        sanitize_svg(NOT_SVG)
