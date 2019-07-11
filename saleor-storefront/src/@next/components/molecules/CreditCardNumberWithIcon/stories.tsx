import React from "react";

import { CreditCardNumberWithIcon } from ".";
import { createStory } from "../baseStory";

createStory("CreditCardNumberWithIcon").add("default", () => (
  <CreditCardNumberWithIcon provider="visa" last4Digits={1234} />
));
