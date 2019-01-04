import { storiesOf } from "@storybook/react";
import * as React from "react";

import * as placeholderImage from "../../../../images/placeholder255x255.png";
import ProductVariantImageSelectDialog from "../../../products/components/ProductVariantImageSelectDialog";
import {
  variantImages as variantImagesFixture,
  variantProductImages as variantProductImagesFixture
} from "../../../products/fixtures";

const variantImages = variantImagesFixture(placeholderImage);
const variantProductImages = variantProductImagesFixture(placeholderImage);

storiesOf("Products / ProductVariantImageSelectDialog", module).add(
  "default",
  () => (
    <ProductVariantImageSelectDialog
      images={variantProductImages}
      selectedImages={variantImages.map(image => image.id)}
      onClose={() => undefined}
      onImageSelect={() => undefined}
      open={true}
    />
  )
);
