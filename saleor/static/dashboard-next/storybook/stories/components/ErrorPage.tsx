import { storiesOf } from "@storybook/react";
import * as React from "react";

import ErrorPage, { ErrorPageProps } from "@components/ErrorPage";
import { Omit } from "@material-ui/core";
import Decorator from "../../Decorator";

const props: Omit<ErrorPageProps, "classes"> = {
  onBack: () => undefined
};

storiesOf("Views / Error page", module)
  .addDecorator(Decorator)
  .add("default", () => <ErrorPage {...props} />);
