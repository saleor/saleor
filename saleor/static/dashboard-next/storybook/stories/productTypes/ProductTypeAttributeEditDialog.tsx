import { storiesOf } from "@storybook/react";
import * as React from "react";

import ProductTypeAttributeEditDialog, {
  ProductTypeAttributeEditDialogProps
} from "../../../productTypes/components/ProductTypeAttributeEditDialog";
import { attributes } from "../../../productTypes/fixtures";
import Decorator from "../../Decorator";

const attribute = attributes[0];

const props: ProductTypeAttributeEditDialogProps = {
  disabled: false,
  errors: [],
  name: attribute.name,
  onClose: () => undefined,
  onConfirm: () => undefined,
  opened: true,
  title: "Add Attribute",
  values: attribute.values.map(value => ({
    label: value.name,
    value: value.id
  }))
};

storiesOf("Product types / Edit attribute", module)
  .addDecorator(Decorator)
  .add("default", () => <ProductTypeAttributeEditDialog {...props} />)
  .add("loading", () => (
    <ProductTypeAttributeEditDialog {...props} disabled={true} />
  ))
  .add("form errors", () => (
    <ProductTypeAttributeEditDialog
      {...props}
      // errors={["name", "values"].map(field => formError(field))}
      errors={["name", "values"].map(field => ({
        field,
        message: "Generic error"
      }))}
    />
  ));
