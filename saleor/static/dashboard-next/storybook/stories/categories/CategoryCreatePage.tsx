import { storiesOf } from "@storybook/react";
import * as React from "react";

import CategoryCreatePage from "../../../categories/components/CategoryCreatePage";
import Decorator from "../../Decorator";

storiesOf("Views / Categories / Create category", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <CategoryCreatePage
      header="Add category"
      disabled={false}
      errors={[]}
      onBack={() => undefined}
    />
  ))
  .add("When loading", () => (
    <CategoryCreatePage
      header="Add category"
      disabled={true}
      errors={[]}
      onBack={() => undefined}
    />
  ));
