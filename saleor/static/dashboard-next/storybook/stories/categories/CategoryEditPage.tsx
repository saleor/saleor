import { storiesOf } from "@storybook/react";
import * as React from "react";

import CategoryEditPage from "../../../categories/components/CategoryEditPage";
import {
  category as categoryFixture,
  errors
} from "../../../categories/fixtures";
import Decorator from "../../Decorator";

const category = categoryFixture("");

storiesOf("Views / Categories / Category edit", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <CategoryEditPage
      category={category}
      onBack={() => undefined}
      onSubmit={() => undefined}
    />
  ))
  .add("when loading", () => (
    <CategoryEditPage
      category={category}
      disabled={true}
      onBack={() => undefined}
      onSubmit={() => undefined}
    />
  ))
  .add("with errors", () => (
    <CategoryEditPage
      category={category}
      errors={errors}
      onBack={() => undefined}
      onSubmit={() => undefined}
    />
  ));
