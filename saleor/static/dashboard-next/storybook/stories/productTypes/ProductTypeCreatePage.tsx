import { Omit } from "@material-ui/core";
import { storiesOf } from "@storybook/react";
import React from "react";

import { formError } from "@saleor/storybook/misc";
import ProductTypeCreatePage, {
  ProductTypeCreatePageProps,
  ProductTypeForm
} from "../../../productTypes/components/ProductTypeCreatePage";
import { WeightUnitsEnum } from "../../../types/globalTypes";
import Decorator from "../../Decorator";

const props: Omit<ProductTypeCreatePageProps, "classes"> = {
  defaultWeightUnit: "kg" as WeightUnitsEnum,
  disabled: false,
  errors: [],
  onBack: () => undefined,
  onSubmit: () => undefined,
  pageTitle: "Create product type",
  saveButtonBarState: "default",
  taxTypes: []
};

storiesOf("Views / Product types / Create product type", module)
  .addDecorator(Decorator)
  .add("default", () => <ProductTypeCreatePage {...props} />)
  .add("loading", () => (
    <ProductTypeCreatePage {...props} disabled={true} pageTitle={undefined} />
  ))
  .add("form errors", () => (
    <ProductTypeCreatePage
      {...props}
      errors={(["name"] as Array<keyof ProductTypeForm>).map(formError)}
    />
  ));
