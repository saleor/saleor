import json
import os
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Self

import nh3

# nh3's default is empty (https://github.com/rust-ammonia/ammonia/blob/6d803b5677006947da7d2f495dbae83090db4909/src/lib.rs#L447).
# Values from EDITOR_JS_ALLOWED_ATTRIBUTE_VALUES are merged on top of these defaults.
DEFAULT_ALLOWED_ATTRIBUTE_VALUES: dict[str, dict[str, set[str]]] = {
    # Allow links to open in a new tab. Rich text can link both to internal pages
    # (e.g. a product description referencing another product) and to external
    # sites (e.g. a vendor page), and the storefront may want to open the latter
    # in a new tab.
    "a": {"target": {"_blank"}},
}


@dataclass
class HtmlCleanerSettings:
    allowed_attributes: dict[str, set[str]] = field(
        default_factory=lambda: deepcopy(nh3.ALLOWED_ATTRIBUTES)
    )

    allowed_attribute_values: dict[str, dict[str, set[str]]] = field(
        default_factory=lambda: deepcopy(DEFAULT_ALLOWED_ATTRIBUTE_VALUES)
    )

    # Configures the 'rel' attribute that will be added on links. `None` disables it.
    #
    # Recommended value: 'noopener noreferrer'
    #
    # - noopener: This prevents a particular type of XSS attack, and should usually be turned on for untrusted HTML.
    # - noreferrer: This prevents the browser from sending the source URL to the website that is linked to.
    # - nofollow: This prevents search engines from using this link for ranking, which disincentivizes spammers.
    #
    # Learn more: https://nh3.readthedocs.io/en/latest/#nh3.Cleaner
    #
    link_rel: str | None = "noopener noreferrer"

    def reload(self) -> Self:
        # NOTE: 'or None' is needed as blank string should be treated as None
        self.link_rel = os.getenv("EDITOR_JS_LINK_REL", "noopener noreferrer") or None

        if allowed_attributes_str := os.getenv("EDITOR_JS_ALLOWED_ATTRIBUTES"):
            for html_tag, allowed_attributes in json.loads(
                allowed_attributes_str
            ).items():
                attr_list = self.allowed_attributes.setdefault(html_tag, set())
                attr_list.update(allowed_attributes)

        if allowed_values_str := os.getenv("EDITOR_JS_ALLOWED_ATTRIBUTE_VALUES"):
            allowed_values: dict[str, dict[str, list[str]]] = json.loads(
                allowed_values_str
            )

            for html_tag, attribute_values in allowed_values.items():
                tag_values = self.allowed_attribute_values.setdefault(html_tag, {})
                for attribute, values in attribute_values.items():
                    tag_values.setdefault(attribute, set()).update(values)
        return self

    @classmethod
    def parse(cls) -> Self:
        return cls().reload()
