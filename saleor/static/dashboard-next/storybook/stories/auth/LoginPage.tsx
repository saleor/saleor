import { storiesOf } from "@storybook/react";
import * as React from "react";

import LoginPage from "../../../auth/components/LoginPage";
import Decorator from "../../Decorator";

storiesOf("Views / Authentication / Log in", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <LoginPage
      error={false}
      onPasswordRecovery={() => {}}
      onSubmit={() => {}}
    />
  ))
  .add("error", () => (
    <LoginPage error={true} onPasswordRecovery={() => {}} onSubmit={() => {}} />
  ));
