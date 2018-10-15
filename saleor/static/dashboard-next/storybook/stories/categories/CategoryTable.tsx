import { storiesOf } from "@storybook/react";
import * as React from "react";

import { categories } from "../../../categories/fixtures";

import CategoryTable from "../../../categories/components/CategoryTable";
import Decorator from "../../Decorator";

const categoryTableProps = {
  categories: categories,
  onAddCategory: undefined,
  onCategoryClick: () => undefined
};

storiesOf("Views / Categories / Category Table", module)
  .addDecorator(Decorator)
  .add("default", () => <CategoryTable {...categoryTableProps} />)
  .add("loading", () => (
    <CategoryTable {...categoryTableProps} categories={undefined} />
  ))
  .add("No data", () => (
    <CategoryTable {...categoryTableProps} categories={[]} />
  ));
