import { storiesOf } from "@storybook/react";
import * as React from "react";

import { Omit } from "@material-ui/core";
import ErrorPage, { ErrorPageProps } from "../../../components/ErrorPage";
import Decorator from "../../Decorator";

const props: Omit<ErrorPageProps, "classes"> = {
  onBack: () => undefined
};

storiesOf("Components / ErrorPage", module)
  .addDecorator(Decorator)
  .add("default", () => <ErrorPage {...props} />);
