import Button from "@material-ui/core/Button";
import { storiesOf } from "@storybook/react";
import * as React from "react";

import withMessages from "../../../components/messages";
import Decorator from "../../Decorator";

storiesOf("Generics / Global messages", module)
  .addDecorator(Decorator)
  .add(
    "default",
    withMessages(({ pushMessage }) => (
      <Button
        color="primary"
        variant="raised"
        onClick={pushMessage({ text: "This is message" })}
      >
        Push message
      </Button>
    ))
  )
  .add(
    "with undo action",
    withMessages(({ pushMessage }) => (
      <Button
        color="primary"
        variant="raised"
        onClick={pushMessage({ text: "This is message", onUndo: () => {} })}
      >
        Push message
      </Button>
    ))
  );
