import { storiesOf } from "@storybook/react";
import * as React from "react";
import * as placeholderImage from "../../../../images/placeholder255x255.png";

import { categories, category } from "../../../categories/fixtures";
import { products as productsFixture } from "../../../products/fixtures";

import CategoryUpdatePage, {
  CategoryUpdatePageProps
} from "../../../categories/components/CategoryUpdatePage";
import Decorator from "../../Decorator";

const products = productsFixture(placeholderImage);

const updateProps: CategoryUpdatePageProps = {
  category,
  disabled: false,
  errors: [],
  loading: false,
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
  products,
  subcategories: categories
};

storiesOf("Views / Categories / Update category", module)
  .addDecorator(Decorator)
  .add("default", () => <CategoryUpdatePage {...updateProps} />)
  .add("no background", () => (
    <CategoryUpdatePage
      {...updateProps}
      category={{ ...category, backgroundImage: null }}
    />
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
      loading={true}
      category={undefined}
    />
  ));
