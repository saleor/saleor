import { storiesOf } from "@storybook/react";
import * as React from "react";

import SaveButtonBar from "../../../components/SaveButtonBar";
import Decorator from "../../Decorator";

const callbacks = {
  onSave: () => {}
};

interface InteractiveDemoProps {
  targetState: "success" | "error" | "string";
}
interface InteractiveDemoState {
  state: "success" | "error" | "loading" | "default";
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
          }, 2000);
        }
      );
    }
  };

  render() {
    return (
      <SaveButtonBar
        onSave={this.handleButtonClick}
        state={this.state.state as any}
      />
    );
  }
}

storiesOf("Generics / SaveButtonBar", module)
  .addDecorator(Decorator)
  .add("idle", () => <SaveButtonBar {...callbacks} />)
  .add("loading", () => <SaveButtonBar {...callbacks} state="loading" />)
  .add("success", () => <SaveButtonBar {...callbacks} state="success" />)
  .add("error", () => <SaveButtonBar {...callbacks} state="error" />)
  .add("disabled", () => <SaveButtonBar {...callbacks} disabled />)
  .add("interactive success", () => <InteractiveDemo targetState="success" />)
  .add("interactive error", () => <InteractiveDemo targetState="error" />);
