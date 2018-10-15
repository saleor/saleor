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
  backgroundImage: category.backgroundImage,
  category,
  disabled: false,
  errors: [],
  loading: false,
  onAddCategory: undefined,
  onAddProduct: undefined,
  onBack: undefined,
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
  products: category.products,
  subcategories: category.children
};

storiesOf("Views / Categories / Update category", module)
  .addDecorator(Decorator)
  .add("default", () => <CategoryUpdatePage {...updateProps} />)
  .add("no background", () => (
    <CategoryUpdatePage {...updateProps} backgroundImage={{}} />
  ))
  .add("loading", () => (
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
