import { storiesOf } from "@storybook/react";
import * as React from "react";

import { category as categoryFixture } from "../../../categories/fixtures";

import CategoryUpdatePage, {
  CategoryUpdatePageProps
} from "../../../categories/components/CategoryUpdatePage";
import Decorator from "../../Decorator";

const category = categoryFixture("");

const updateProps: CategoryUpdatePageProps = {
  category: category,
  subcategories: category.children,
  disabled: false,
  errors: [],
  products: category.products,
  loading: false,
  pageInfo: {
    hasNextPage: true,
    hasPreviousPage: true
  },
  onNextPage: undefined,
  onPreviousPage: undefined,
  onProductClick: () => undefined,
  onAddProduct: undefined,
  onCategoryClick: () => undefined,
  onAddCategory: undefined,
  onBack: undefined,
  onDelete: undefined
};

storiesOf("Views / Categories / Update category", module)
  .addDecorator(Decorator)
  .add("default", () => <CategoryUpdatePage {...updateProps} />)
  .add("When in root", () => (
    <CategoryUpdatePage
      {...updateProps}
      products={undefined}
      category={undefined}
    />
  ))
  .add("When loading", () => (
    <CategoryUpdatePage
      {...updateProps}
      subcategories={undefined}
      disabled={true}
      products={undefined}
      loading={true}
    />
  ));
