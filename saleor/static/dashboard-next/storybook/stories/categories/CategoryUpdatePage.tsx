import { storiesOf } from "@storybook/react";
import * as React from "react";

import { category as categoryFixture } from "../../../categories/fixtures";

import CategoryUpdatePage from "../../../categories/components/CategoryUpdatePage";
import Decorator from "../../Decorator";

const category = categoryFixture("");

storiesOf("Views / Categories / Update category", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <CategoryUpdatePage header={category.name} category={category} />
  ));
