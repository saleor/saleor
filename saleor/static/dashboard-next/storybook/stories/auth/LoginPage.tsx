import { Omit } from "@material-ui/core";
import { storiesOf } from "@storybook/react";
import * as React from "react";

import LoginPage, { LoginCardProps } from "../../../auth/components/LoginPage";
import Decorator from "../../Decorator";

const props: Omit<LoginCardProps, "classes"> = {
  disableLoginButton: true,
  error: false,
  onPasswordRecovery: undefined,
  onSubmit: () => undefined
};

storiesOf("Views / Authentication / Log in", module)
  .addDecorator(Decorator)
  .add("default", () => <LoginPage {...props} />)
  .add("error", () => <LoginPage {...props} error={true} />)
  .add("loading", () => <LoginPage {...props} disableLoginButton={true} />);
