import Button from "@material-ui/core/Button";
import { storiesOf } from "@storybook/react";
import * as React from "react";

import Messages from "../../../components/messages";
import Decorator from "../../Decorator";

storiesOf("Generics / Global messages", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <Messages>
      {pushMessage => (
        <Button
          color="primary"
          variant="contained"
          onClick={() => pushMessage({ text: "This is message" })}
        >
          Push message
        </Button>
      )}
    </Messages>
  ))
  .add("with undo action", () => (
    <Messages>
      {pushMessage => (
        <Button
          color="primary"
          variant="contained"
          onClick={() =>
            pushMessage({ text: "This is message", onUndo: undefined })
          }
        >
          Push message
        </Button>
      )}
    </Messages>
  ));
