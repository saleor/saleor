import { storiesOf } from "@storybook/react";
import * as React from "react";
import * as placeholderImage from "../../../../images/placeholder255x255.png";

import { category as categoryFixture } from "../../../categories/fixtures";

import CategoryUpdatePage, {
  CategoryUpdatePageProps
} from "../../../categories/components/CategoryUpdatePage";
import Decorator from "../../Decorator";

const category = categoryFixture(placeholderImage);

const updateProps: CategoryUpdatePageProps = {
  category: category,
  subcategories: category.children,
  backgroundImage: category.backgroundImage,
  placeholderImage: placeholderImage,
  disabled: false,
  errors: [],
  products: category.products,
  loading: false,
  pageInfo: {
    hasNextPage: true,
    hasPreviousPage: true
  },
  onNextPage: undefined,
  onSubmit: () => undefined,
  onPreviousPage: undefined,
  onImageDelete: () => undefined,
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
  .add("default without background", () => (
    <CategoryUpdatePage {...updateProps} backgroundImage={{}} />
  ))
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
      category={undefined}
      backgroundImage={undefined}
    />
  ));
