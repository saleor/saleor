import { storiesOf } from "@storybook/react";
import React from "react";

import { Omit } from "@material-ui/core";
import ErrorPage, { ErrorPageProps } from "@saleor/components/ErrorPage";
import Decorator from "../../Decorator";

const props: Omit<ErrorPageProps, "classes"> = {
  onBack: () => undefined
};

storiesOf("Views / Error page", module)
  .addDecorator(Decorator)
  .add("default", () => <ErrorPage {...props} />);
