import { storiesOf } from "@storybook/react";
import * as React from "react";

import NotFoundPage from "../../../components/NotFoundPage";
import Decorator from "../../Decorator";

storiesOf("Views / Not found error page", module)
  .addDecorator(Decorator)
  .add("default", () => <NotFoundPage onBack={() => undefined} />);
