import { storiesOf } from "@storybook/react";
import * as React from "react";

import CategoryListPage from "../../../categories/components/CategoryListPage";
import { categories } from "../../../categories/fixtures";
import Decorator from "../../Decorator";

const categoryTableProps = {
  categories,
  onAddCategory: undefined,
  onCategoryClick: () => undefined
};

storiesOf("Views / Categories / Category list", module)
  .addDecorator(Decorator)
  .add("default", () => <CategoryListPage {...categoryTableProps} />)
  .add("loading", () => (
    <CategoryListPage {...categoryTableProps} categories={undefined} />
  ))
  .add("empty", () => (
    <CategoryListPage {...categoryTableProps} categories={[]} />
  ));
