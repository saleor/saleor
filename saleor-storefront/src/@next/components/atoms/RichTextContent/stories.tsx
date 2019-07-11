import React from "react";

import { RichTextContent } from ".";
import { createStory } from "../baseStory";
import descriptionJson from "./fixtures/default_text_block";
import customDescriptionJson from "./fixtures/text_blocks";

createStory("RichTextContent")
  .add("default", () => <RichTextContent descriptionJson={descriptionJson} />)
  .add("custom", () => (
    <RichTextContent descriptionJson={customDescriptionJson} />
  ));
