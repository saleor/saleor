import { storiesOf } from "@storybook/react";
import * as React from "react";

import ProductVariantDeleteDialog from "../../../products/components/ProductVariantDeleteDialog";
import { variant } from "../../../products/fixtures";

storiesOf("Products / ProductVariantDeleteDialog", module).add(
  "default",
  () => <ProductVariantDeleteDialog open={true} name={variant("").name} />
);
