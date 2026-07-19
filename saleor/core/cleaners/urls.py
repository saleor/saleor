import ipaddress
import urllib.parse
from typing import Protocol

import idna

MAILTO_SAFE_CHARS = ".-_+,"


class UrlCleaner(Protocol):
    def __call__(self, dirty_url: str) -> str: ...


class URLCleanerError(ValueError):
    """Base exception class for all URL cleaner-related exceptions."""


class InvalidHostname(URLCleanerError):
    """Raised when an invalid domain or hostname is provided."""


class InvalidURL(URLCleanerError):
    """Raised when the URL syntax is wrong."""


class InvalidUsage(RuntimeError):
    """Raised when a cleaner function wasn't used properly, indicates a code bug."""


def normalize_host(dirty_domain: str) -> str:
    """Normalize a hostname/domain field."""

    dirty_domain = dirty_domain.lower()

    # If it's an IPv6 address, then try to parse it and return the normalized
    # value from Python's ipaddress module
    if dirty_domain.startswith("["):
        dirty_domain = dirty_domain.strip("[]")
        try:
            clean_ip = str(ipaddress.IPv6Address(dirty_domain))
            return f"[{clean_ip}]"
        except ipaddress.AddressValueError as exc:
            raise InvalidHostname("Invalid IPv6 address") from exc

    # If it's not IPv6, then we use idna to validate & to normalize
    try:
        parts = [
            idna.encode(
                part,
                strict=True,
                std3_rules=True,  # Follows RFC 1123 for the hostname
            ).decode("utf-8")
            for part in dirty_domain.split(".")
        ]
    except idna.IDNAError as exc:
        raise InvalidHostname("Invalid characters found in hostname") from exc

    return ".".join(parts)


def clean_tel(dirty_url: str) -> str:
    """Clean a 'tel' URL (e.g., 'tel:+3312345678')."""

    scheme, _, dirty_tel = dirty_url.partition(":")

    # This should never happen, as a safeguard we are raising
    if scheme != "tel":
        raise InvalidUsage(f"Expected url scheme to be 'tel', found {scheme} instead")
    # Keeps special characters listed by RFC 3966 as is, and encodes anything else
    # (such as dangerous characters like "<>)
    cleaned_path = urllib.parse.quote(dirty_tel, safe="+-.()*#;=%")
    return f"tel:{cleaned_path}"


def clean_mailto(
    dirty_url: str,
    *,
    max_address_count: int = 10,
    max_header_count: int = 10,
) -> str:
    """Clean a mailto URL based on RFC 6068 (leniently)."""

    scheme, _, dirty_url = dirty_url.partition(":")

    if scheme != "mailto":
        raise InvalidUsage(
            f"Expected url scheme to be 'mailto', found {scheme} instead"
        )

    # raw_dirty_addr_list is the address list before the '?' character, e.g., from:
    # `foo@example.com?body=text`
    raw_dirty_addr_list, _, raw_dirty_qs = dirty_url.partition("?")

    # Retrieves the list of email addresses before the '?' delimiter (if any)
    #
    # Note: an empty list of addresses is allowed (per RFC 6068), i.e.,
    #       the user can do `mailto:?<headers>` instead of
    #       `mailto:foo@example.com?<headers>` - this is used for things like:
    #       `mailto:?To=foo@example.com,bar@example.com,...`
    #
    #       Thus we shouldn't raise if we see an empty list.
    if raw_dirty_addr_list:
        dirty_addr_list = raw_dirty_addr_list.split(",", maxsplit=max_address_count + 1)
        if len(dirty_addr_list) > max_address_count:
            raise InvalidURL("Too many addresses in mailto URL")
    else:
        dirty_addr_list = []

    cleaned_addresses = []
    for dirty_addr in dirty_addr_list:
        # Example: user@domain
        dirty_local_part, _, dirty_domain = dirty_addr.partition("@")

        if not all((dirty_local_part, dirty_domain)):
            raise InvalidURL("Invalid email address")

        dirty_local_part = urllib.parse.unquote(dirty_local_part)
        clean_local_part = urllib.parse.quote(dirty_local_part, safe=MAILTO_SAFE_CHARS)

        dirty_domain = urllib.parse.unquote(dirty_domain)
        clean_domain = normalize_host(dirty_domain)
        cleaned_addresses.append(f"{clean_local_part}@{clean_domain}")

    cleaned_url = "mailto:"
    if cleaned_addresses:
        cleaned_url += ",".join(cleaned_addresses)

    # Clean the email headers (query), the RFC specs are similar to HTTP URLs
    # thus we can use urllib
    if raw_dirty_qs:
        headers_dict = urllib.parse.parse_qs(
            raw_dirty_qs, max_num_fields=max_header_count
        )
        cleaned_raw_headers = urllib.parse.urlencode(
            headers_dict,
            doseq=True,
            safe=f"{MAILTO_SAFE_CHARS}@",
            quote_via=urllib.parse.quote,
        )
        cleaned_url += f"?{cleaned_raw_headers}"

    return cleaned_url


URL_SCHEME_CLEANERS: dict[str, UrlCleaner] = {"mailto": clean_mailto, "tel": clean_tel}
