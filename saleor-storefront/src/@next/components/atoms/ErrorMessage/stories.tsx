import React from "react";

import { ErrorMessage } from ".";
import { createStory } from "../baseStory";

const ERRORS = [{ field: "Field", message: "Error Message" }];

createStory("ErrorMessage")
  .add("default", () => <ErrorMessage errors={ERRORS} />)
  .add("with multiple errors", () => (
    <ErrorMessage errors={[...ERRORS, ...ERRORS]} />
  ));
