import { storiesOf } from "@storybook/react";
import * as React from "react";

import ProductTypeDetailsPage from "../../../productTypes/components/ProductTypeDetailsPage";
import { attributes, productType } from "../../../productTypes/fixtures";
import { WeightUnitsEnum } from "../../../types/globalTypes";
import Decorator from "../../Decorator";

const props = {
  defaultWeightUnit: "kg" as WeightUnitsEnum,
  disabled: false,
  errors: [],
  onAttributeSearch: () => undefined,
  onBack: () => undefined,
  onDelete: () => undefined,
  onSubmit: () => undefined,
  pageTitle: productType.name,
  productType,
  saveButtonBarState: "default",
  searchLoading: false,
  searchResults: attributes
};

storiesOf("Views / Product types / Product type details", module)
  .addDecorator(Decorator)
  .add("default", () => <ProductTypeDetailsPage {...props} />)
  .add("loading", () => (
    <ProductTypeDetailsPage
      {...props}
      disabled={true}
      pageTitle={undefined}
      productType={undefined}
    />
  ));
