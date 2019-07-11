import React from "react";

import { IconButton } from ".";
import { createStory } from "../baseStory";

createStory("IconButton")
  .add("edit icon button", () => <IconButton name="edit" size={19} />)
  .add("trash icon button", () => <IconButton name="trash" size={22} />);
