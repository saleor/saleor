import { storiesOf } from "@storybook/react";
import * as React from "react";

import { category as categoryFixture } from "../../../categories/fixtures";

import CategoryUpdatePage from "../../../categories/components/CategoryUpdatePage";
import Decorator from "../../Decorator";

const category = categoryFixture("");

storiesOf("Views / Categories / Update category", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <CategoryUpdatePage
      subcategories={category.children}
      disabled={false}
      category={category}
      errors={[]}
      products={category.products}
      loading={false}
      pageInfo={{
        hasNextPage: true,
        hasPreviousPage: true
      }}
      onNextPage={undefined}
      onPreviousPage={undefined}
      onProductClick={() => undefined}
      onAddProduct={undefined}
      onCategoryClick={() => undefined}
      onAddCategory={undefined}
    />
  ))
  .add("When in root", () => (
    <CategoryUpdatePage
      subcategories={category.children}
      disabled={false}
      errors={[]}
      loading={false}
      category={undefined}
      onNextPage={undefined}
      onPreviousPage={undefined}
      onProductClick={() => undefined}
      onAddProduct={undefined}
      onCategoryClick={() => undefined}
      onAddCategory={undefined}
    />
  ))
  .add("When loading", () => (
    <CategoryUpdatePage
      subcategories={undefined}
      disabled={false}
      category={category}
      errors={[]}
      products={undefined}
      loading={true}
      onProductClick={() => undefined}
      onCategoryClick={() => undefined}
    />
  ));
