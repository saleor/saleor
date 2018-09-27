import { storiesOf } from "@storybook/react";
import * as React from "react";

import ProductTypeDetailsPage from "../../../productTypes/components/ProductTypeDetailsPage";
import { attributes, productType } from "../../../productTypes/fixtures";
import Decorator from "../../Decorator";

storiesOf("Views / Product types / Product type details", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <ProductTypeDetailsPage
      disabled={false}
      errors={[]}
      pageTitle={productType.name}
      productType={productType}
      productAttributes={productType.productAttributes}
      variantAttributes={productType.variantAttributes}
      saveButtonBarState="default"
      searchLoading={false}
      searchResults={attributes}
      onAttributeSearch={undefined}
      onBack={() => undefined}
      onDelete={undefined}
      onSubmit={() => undefined}
    />
  ))
  .add("loading", () => (
    <ProductTypeDetailsPage
      disabled={true}
      errors={[]}
      pageTitle={undefined}
      saveButtonBarState="default"
      searchLoading={false}
      searchResults={[]}
      onAttributeSearch={undefined}
      onBack={() => undefined}
      onDelete={undefined}
      onSubmit={() => undefined}
    />
  ));
