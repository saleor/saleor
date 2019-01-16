import { storiesOf } from "@storybook/react";
import * as React from "react";

import { ConfirmButtonTransitionState } from "../../../components/ConfirmButton/ConfirmButton";
import SaveButtonBar from "../../../components/SaveButtonBar";
import Decorator from "../../Decorator";

const props = {
  disabled: false,
  onCancel: undefined,
  onDelete: undefined,
  onSave: undefined,
  state: "default" as ConfirmButtonTransitionState
};

interface InteractiveDemoProps {
  targetState: "success" | "error" | "string";
}
interface InteractiveDemoState {
  state: ConfirmButtonTransitionState;
}

class InteractiveDemo extends React.Component<
  InteractiveDemoProps,
  InteractiveDemoState
> {
  state = {
    state: "default" as "default"
  };
  timer = undefined;

  componentWillUnmount() {
    clearTimeout(this.timer);
  }

  handleButtonClick = () => {
    if ((this.state.state as string) !== "loading") {
      this.setState(
        {
          state: "loading"
        },
        () => {
          this.timer = setTimeout(() => {
            this.setState({
              state: this.props.targetState as "success" | "error"
            });
          }, 3000);
        }
      );
    }
  };

  render() {
    return (
      <SaveButtonBar
        disabled={false}
        onCancel={() => undefined}
        onSave={this.handleButtonClick}
        state={this.state.state}
      />
    );
  }
}

storiesOf("Generics / SaveButtonBar", module)
  .addDecorator(Decorator)
  .add("idle", () => <SaveButtonBar {...props} state="default" />)
  .add("loading", () => <SaveButtonBar {...props} state="loading" />)
  .add("success", () => <SaveButtonBar {...props} state="success" />)
  .add("error", () => <SaveButtonBar {...props} state="error" />)
  .add("disabled", () => <SaveButtonBar {...props} disabled />)
  .add("interactive success", () => <InteractiveDemo targetState="success" />)
  .add("interactive error", () => <InteractiveDemo targetState="error" />);
