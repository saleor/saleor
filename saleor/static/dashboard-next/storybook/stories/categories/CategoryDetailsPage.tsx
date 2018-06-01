import { storiesOf } from "@storybook/react";
import * as React from "react";

import CategoryDetailsPage from "../../../categories/components/CategoryDetailsPage";
import Decorator from "../../Decorator";

storiesOf("Categories / CategoryDetailsPage", module)
  .addDecorator(Decorator)
  .add("default", () => <CategoryDetailsPage />)
  .add("other", () => <CategoryDetailsPage />);
