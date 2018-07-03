import { storiesOf } from "@storybook/react";
import * as React from "react";

import messages from "../../../components/messages";
import Decorator from "../../Decorator";

storiesOf("Components / messages", module)
  .addDecorator(Decorator)
  .add("default", () => <messages />)
  .add("other", () => <messages />);
