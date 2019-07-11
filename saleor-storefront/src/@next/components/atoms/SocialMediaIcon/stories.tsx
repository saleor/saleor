import React from "react";

import { SocialMediaIcon } from ".";
import { createStory } from "../baseStory";
import { Medium } from "./types";

const FACEBOOK_MEDIUM: Medium = {
  ariaLabel: "facebook",
  href: "https://www.facebook.com/mirumeelabs/",
  iconName: "social_facebook",
};

createStory("SocialMediaIcon").add("sample medium", () => (
  <SocialMediaIcon medium={FACEBOOK_MEDIUM} key={FACEBOOK_MEDIUM.ariaLabel} />
));
