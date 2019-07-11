import { storiesOf } from "@storybook/react";
import React from "react";

import LoginLoading from "../../../auth/components/LoginLoading";
import Decorator from "../../Decorator";

storiesOf("Views / Authentication / Verifying remembered user", module)
  .addDecorator(Decorator)
  .add("default", () => <LoginLoading />);
