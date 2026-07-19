import json
import os
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Self

import nh3


@dataclass
class HtmlCleanerSettings:
    allowed_attributes: dict[str, set[str]] = field(
        default_factory=lambda: deepcopy(nh3.ALLOWED_ATTRIBUTES)
    )

    # NOTE: nh3 doesn't expose the default values, however it's OK as
    #       the default value is empty https://github.com/rust-ammonia/ammonia/blob/6d803b5677006947da7d2f495dbae83090db4909/src/lib.rs#L447
    allowed_attribute_values: dict[str, dict[str, set[str]]] = field(
        default_factory=dict
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

            # Converts raw values' list[str] to set[str] type as nh3 wants `set[str]`
            for key, nested_dict in allowed_values.items():
                self.allowed_attribute_values[key] = {
                    k: set(v) for k, v in nested_dict.items()
                }
        return self

    @classmethod
    def parse(cls) -> Self:
        return cls().reload()
