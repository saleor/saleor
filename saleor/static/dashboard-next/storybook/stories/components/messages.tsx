import Button from "@material-ui/core/Button";
import { storiesOf } from "@storybook/react";
import * as React from "react";

import useNotifier from "../../../hooks/useNotifier";
import Decorator from "../../Decorator";

storiesOf("Generics / Global messages", module)
  .addDecorator(Decorator)
  .add("default", () => {
    const pushMessage = useNotifier();

    return (
      <Button
        color="primary"
        variant="contained"
        onClick={() => pushMessage({ text: "This is message" })}
      >
        Push message
      </Button>
    );
  })
  .add("with undo action", () => {
    const pushMessage = useNotifier();

    return (
      <Button
        color="primary"
        variant="contained"
        onClick={() =>
          pushMessage({ text: "This is message", onUndo: undefined })
        }
      >
        Push message
      </Button>
    );
  });
