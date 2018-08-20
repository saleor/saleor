import { storiesOf } from "@storybook/react";
import * as React from "react";

import LoginPage from "../../../auth/components/LoginPage";
import Decorator from "../../Decorator";

storiesOf("Views / Authentication / Log in", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <LoginPage
      error={false}
      onPasswordRecovery={undefined}
      onSubmit={() => undefined}
    />
  ))
  .add("error", () => (
    <LoginPage
      error={true}
      onPasswordRecovery={undefined}
      onSubmit={() => undefined}
    />
  ));
