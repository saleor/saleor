import { storiesOf } from "@storybook/react";
import * as React from "react";

import ProductTypeDetailsPage from "../../../productTypes/components/ProductTypeDetailsPage";
import { attributes, productType } from "../../../productTypes/fixtures";
import Decorator from "../../Decorator";

const taxRates = ["standard", "electronics", "food", "apparel"];

storiesOf("Views / Product types / Product type details", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <ProductTypeDetailsPage
      disabled={false}
      pageTitle={productType.name}
      productType={productType}
      productAttributes={productType.productAttributes.edges.map(
        edge => edge.node
      )}
      variantAttributes={productType.variantAttributes.edges.map(
        edge => edge.node
      )}
      saveButtonBarState="default"
      searchLoading={false}
      searchResults={attributes}
      taxRates={taxRates}
      onAttributeSearch={undefined}
      onBack={() => undefined}
      onDelete={undefined}
      onSubmit={() => undefined}
    />
  ))
  .add("loading", () => (
    <ProductTypeDetailsPage
      disabled={true}
      pageTitle={undefined}
      saveButtonBarState="default"
      searchLoading={false}
      searchResults={[]}
      taxRates={[]}
      onAttributeSearch={undefined}
      onBack={() => undefined}
      onDelete={undefined}
      onSubmit={() => undefined}
    />
  ));
