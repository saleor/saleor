import { Omit } from "@material-ui/core";
import { storiesOf } from "@storybook/react";
import * as React from "react";
import * as placeholderImage from "../../../../images/placeholder255x255.png";

import { category as categoryFixture } from "../../../categories/fixtures";

import CategoryUpdatePage, {
  CategoryUpdatePageProps
} from "../../../categories/components/CategoryUpdatePage";
import Decorator from "../../Decorator";

const category = categoryFixture(placeholderImage);

const updateProps: Omit<CategoryUpdatePageProps, "classes"> = {
  category,
  disabled: false,
  errors: [],
  onAddCategory: undefined,
  onAddProduct: undefined,
  onBack: () => undefined,
  onCategoryClick: () => undefined,
  onDelete: () => undefined,
  onImageDelete: () => undefined,
  onImageUpload: () => undefined,
  onNextPage: undefined,
  onPreviousPage: undefined,
  onProductClick: () => undefined,
  onSubmit: () => undefined,
  pageInfo: {
    hasNextPage: true,
    hasPreviousPage: true
  },
  placeholderImage,
  products: category.products.edges.map(edge => edge.node),
  saveButtonBarState: "default",
  subcategories: category.children.edges.map(edge => edge.node)
};

storiesOf("Views / Categories / Update category", module)
  .addDecorator(Decorator)
  .add("default", () => <CategoryUpdatePage {...updateProps} />)
  .add("no background", () => (
    <CategoryUpdatePage {...updateProps} category={category} />
  ))
  .add("no subcategories", () => (
    <CategoryUpdatePage {...updateProps} subcategories={[]} />
  ))
  .add("no products", () => (
    <CategoryUpdatePage {...updateProps} products={[]} />
  ))
  .add("loading", () => (
    <CategoryUpdatePage
      {...updateProps}
      subcategories={undefined}
      disabled={true}
      products={undefined}
      category={undefined}
    />
  ));
