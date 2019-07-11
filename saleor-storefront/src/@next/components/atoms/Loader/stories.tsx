import { boolean } from "@storybook/addon-knobs";
import React from "react";

import { Loader } from ".";
import { createStory } from "../baseStory";

createStory("Loader").add("default", () => (
  <Loader fullScreen={boolean("Fullscreen", false)} />
));
