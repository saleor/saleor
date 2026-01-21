import pytest

from ..urls import clean_mailto, clean_tel


@pytest.mark.parametrize(
    "input_url",
    [
        # All valid inputs (should be unchanged by the cleaner)
        "tel:1234567890",
        "tel:+1234567890",
        "tel:+1-202-555-0123",
        "tel:+1(202)555.0123",
        "tel:*123#",
        "tel:#21#",
        "tel:+49(30)123456",
        "tel:123;ext=456",
        "tel:+1;phone-context=example.com",
        "tel:+1;isub=12345",
        "tel:+123%;ext=1",
        "tel:1-2-3-4-5",
        "tel:1...(2)...3",
        "tel:((123))",
        "tel:+1.-()",
        "tel:",
        "tel:+",
        "tel:*",
        "tel:#",
    ],
)
def test_clean_url_tel_scheme_valid(input_url: str):
    """Test valid `tel` URL inputs are unchanged (RFC 3966)."""
    actual = clean_tel(input_url)
    assert actual == input_url, "URL shouldn't have been changed"


@pytest.mark.parametrize(
    ("input_url", "expected_cleaned_url"),
    [
        # It must be 'tel:' not 'tel://'
        ("tel://", "tel:%2F%2F"),
        ('tel:+3300"<>', "tel:+3300%22%3C%3E"),
        ("tel:+3300\n", "tel:+3300%0A"),
        # Ensures all parts/components are quoted
        ('tel:"\n#"\n;"\n', "tel:%22%0A#%22%0A;%22%0A"),
    ],
)
def test_clean_url_tel_scheme_invalid(input_url: str, expected_cleaned_url: str):
    """Test invalid characters in `tel` URLs are quoted."""
    actual = clean_tel(input_url)
    assert actual == expected_cleaned_url


@pytest.mark.parametrize(
    ("input_url", "changed_to"),
    [
        ("mailto:", None),
        ("mailto:chris@[::1]", None),  # IPv6 should work
        (
            # Should quote all parts
            'mailto:"@example.com?"="',
            "mailto:%22@example.com?%22=%22",
        ),
        (
            # Should quote all parts, including control characters
            "mailto:\n@example.com?\n=\n",
            "mailto:%0A@example.com?%0A=%0A",
        ),
        # Based on https://www.rfc-editor.org/rfc/rfc6068#section-6
        ("mailto:chris@example.com", None),
        ("mailto:infobot@example.com?subject=current-issue", None),
        ("mailto:infobot@example.com?body=send%20current-issue", None),
        (
            "mailto:infobot@example.com?body=send%20current-issue%0D%0Asend%20index",
            None,
        ),
        ("mailto:list@example.org?In-Reply-To=%3C3469A91.D10AF4C@example.com%3E", None),
        ("mailto:majordomo@example.com?body=subscribe%20bamboo-l", None),
        ("mailto:joe@example.com?cc=bob@example.com&body=hello", None),
        ("mailto:?to=addr1@an.example,addr2@an.example", None),
        ("mailto:addr1@an.example?to=addr2@an.example", None),
        ("mailto:%22not%40me%22@example.org", None),
        ("mailto:%22oh%5C%5Cno%22@example.org", None),
        (
            "mailto:%22%5C%5C%5C%22it's%5C%20ugly%5C%5C%5C%22%22@example.org",
            # We don't allow single quotes (')
            "mailto:%22%5C%5C%5C%22it%27s%5C%20ugly%5C%5C%5C%22%22@example.org",
        ),
        ("mailto:user@example.org?subject=caf%C3%A9", None),
        ("mailto:user@example.org?subject=%3D%3Futf-8%3FQ%3Fcaf%3DC3%3DA9%3F%3D", None),
        ("mailto:user@example.org?subject=%3D%3Fiso-8859-1%3FQ%3Fcaf%3DE9%3F%3D", None),
        ("mailto:user@example.org?subject=caf%C3%A9&body=caf%C3%A9", None),
        (
            "mailto:user@%E7%B4%8D%E8%B1%86.example.org?subject=Test&body=NATTO",
            # We IDNA encode unicode characters
            "mailto:user@xn--99zt52a.example.org?subject=Test&body=NATTO",
        ),
        # Shouldn't be getting re-quoted when something was already quoted (%25)
        ("mailto:foo%25bar@example.com", None),
    ],
)
def test_clean_url_mailto_scheme_valid(input_url: str, changed_to: str | None):
    """Test valid `mailto` URL inputs are unchanged (RFC 6068)."""
    changed_to = changed_to or input_url
    actual = clean_mailto(input_url)
    assert actual == changed_to


@pytest.mark.parametrize(
    ("_case", "input_url", "expected_error"),
    [
        (
            "rejects mailto URIs that contain too many addresses",
            "mailto:" + ",".join(["user@example.com"] * 11),
            "Too many addresses in mailto URL",
        ),
        (
            "rejects invalid domains",
            'mailto:foo@Exam"ple.com',
            "Invalid characters found in hostname",
        ),
        ("rejects invalid IPv6", "mailto:chris@[not-an-ip]", "Invalid IPv6 address"),
    ],
)
def test_clean_url_mailto_scheme_invalid_urls(
    _case: str, input_url: str, expected_error: str
):
    with pytest.raises(ValueError, match=expected_error):
        clean_mailto(input_url)
