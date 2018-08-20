import { storiesOf } from "@storybook/react";
import * as React from "react";

import * as placeholderImage from "../../../../images/placeholder60x60.png";
import CategoryDetailsPage from "../../../categories/components/CategoryDetailsPage";
import { category as categoryFixture } from "../../../categories/fixtures";
import Decorator from "../../Decorator";

const category = categoryFixture(placeholderImage);

storiesOf("Views / Categories / Category details", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <CategoryDetailsPage
      category={category}
      subcategories={category.children}
      products={category.products}
      pageInfo={{
        hasNextPage: true,
        hasPreviousPage: true
      }}
      loading={false}
      onAddCategory={undefined}
      onAddProduct={undefined}
      onBack={() => undefined}
      onCategoryClick={() => undefined}
      onDelete={undefined}
      onEdit={undefined}
      onNextPage={undefined}
      onPreviousPage={undefined}
      onProductClick={() => undefined}
    />
  ))
  .add("when in root", () => (
    <CategoryDetailsPage
      subcategories={category.children}
      loading={false}
      onAddCategory={undefined}
      onAddProduct={undefined}
      onBack={() => undefined}
      onCategoryClick={() => undefined}
      onDelete={undefined}
      onEdit={undefined}
      onNextPage={undefined}
      onPreviousPage={undefined}
      onProductClick={() => undefined}
    />
  ))
  .add("when loading", () => <CategoryDetailsPage loading={true} />);
