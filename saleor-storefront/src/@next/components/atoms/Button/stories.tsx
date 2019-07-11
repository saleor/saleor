import React from "react";

import { Button } from ".";
import { createStory } from "../baseStory";

createStory("Button")
  .add("Primary", () => <Button>Primary Button</Button>)
  .add("Secondary", () => <Button color="secondary">Secondary Button</Button>);
