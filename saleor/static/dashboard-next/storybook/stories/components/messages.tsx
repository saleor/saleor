import Button from "@material-ui/core/Button";
import { storiesOf } from "@storybook/react";
import * as React from "react";

import useNotifier from "../../../hooks/useNotifier";
import Decorator from "../../Decorator";

interface StoryProps {
  undo: boolean;
}
const Story: React.FC<StoryProps> = ({ undo }) => {
  const pushMessage = useNotifier();

  return (
    <Button
      color="primary"
      variant="contained"
      onClick={() =>
        pushMessage({
          onUndo: undo ? () => undefined : undefined,
          text: "This is message"
        })
      }
    >
      Push message
    </Button>
  );
};

storiesOf("Generics / Global messages", module)
  .addDecorator(Decorator)
  .add("default", () => <Story undo={false} />)
  .add("with undo action", () => <Story undo={true} />);
