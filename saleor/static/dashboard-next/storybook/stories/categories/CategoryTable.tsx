import { storiesOf } from "@storybook/react";
import * as React from "react";

import { categories } from "../../../categories/fixtures";

import CategoryTable from "../../../categories/components/CategoryTable";
import Decorator from "../../Decorator";

storiesOf("Views / Categories / Category Table", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <CategoryTable
      categories={categories}
      onAddCategory={undefined}
      onCategoryClick={() => undefined}
    />
  ));
