import Button from "@material-ui/core/Button";
import { storiesOf } from "@storybook/react";
import * as React from "react";

import withMessages from "../../../components/messages";
import Decorator from "../../Decorator";

storiesOf("Components / messages", module)
  .addDecorator(Decorator)
  .add("default", () =>
    withMessages(pushMessage => (
      <Button
        onClick={pushMessage({ text: "This is message" })}
        variant="raised"
      >
        Push message
      </Button>
    ))
  )
  .add("other", () =>
    withMessages(pushMessage => (
      <Button
        onClick={pushMessage({ text: "This is message", onUndo: () => {} })}
        variant="raised"
      >
        Push message
      </Button>
    ))
  );
