import { storiesOf } from "@storybook/react";
import * as React from "react";

import ErrorPage, { ErrorPageProps } from "../../../components/ErrorPage";
import Decorator from "../../Decorator";

const props:ErrorPageProps = {

}

storiesOf("Components / ErrorPage", module)
  .addDecorator(Decorator)
  .add("default", () => <ErrorPage {...ErrorPageProps} />)
  .add("other", () => <ErrorPage {...ErrorPageProps} />);
