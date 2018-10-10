import { storiesOf } from "@storybook/react";
import * as React from "react";

import CategoryDeleteDialog from "../../../categories/components/CategoryDeleteDialog";
import { category as categoryFixture } from "../../../categories/fixtures";
import Decorator from "../../Decorator";

const category = categoryFixture("");

storiesOf("Categories / CategoryDeleteDialog", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <CategoryDeleteDialog
      name={category.name}
      open={true}
      onClose={undefined}
      onConfirm={undefined}
    />
  ))
  .add("with products", () => (
    <CategoryDeleteDialog
      name={category.name}
      open={true}
      onClose={undefined}
      onConfirm={undefined}
    />
  ));
