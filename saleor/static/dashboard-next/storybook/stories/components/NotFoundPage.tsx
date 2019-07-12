import { storiesOf } from "@storybook/react";
import React from "react";

import NotFoundPage from "@saleor/components/NotFoundPage";
import Decorator from "../../Decorator";

storiesOf("Views / Not found error page", module)
  .addDecorator(Decorator)
  .add("default", () => <NotFoundPage onBack={() => undefined} />);
