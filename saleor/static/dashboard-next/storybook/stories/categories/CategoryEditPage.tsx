import { storiesOf } from "@storybook/react";
import * as React from "react";

import CategoryEditPage from "../../../categories/components/CategoryEditPage";
// import Decorator from "../../Decorator";
import {
  category as categoryFixture,
  errors
} from "../../../categories/fixtures";

const category = categoryFixture("");

storiesOf("Views / Categories / Category edit", module)
  // .addDecorator(Decorator)
  .add("default", () => (
    <CategoryEditPage
      description={category.description}
      name={category.name}
      onBack={() => {}}
      onSubmit={() => {}}
    />
  ))
  .add("when loading", () => (
    <CategoryEditPage
      description={category.description}
      loading={true}
      name={category.name}
      onBack={() => {}}
      onSubmit={() => {}}
    />
  ))
  .add("with errors", () => (
    <CategoryEditPage
      description={category.description}
      errors={errors}
      name={category.name}
      onBack={() => {}}
      onSubmit={() => {}}
    />
  ));
