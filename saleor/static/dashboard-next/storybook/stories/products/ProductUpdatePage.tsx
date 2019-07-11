import { storiesOf } from "@storybook/react";
import React from "react";

import { collections } from "@saleor/collections/fixtures";
import { listActionsProps } from "@saleor/fixtures";
import ProductUpdatePage, {
  ProductUpdatePageProps
} from "@saleor/products/components/ProductUpdatePage";
import { product as productFixture } from "@saleor/products/fixtures";
import placeholderImage from "../../../../images/placeholder255x255.png";
import Decorator from "../../Decorator";

const product = productFixture(placeholderImage);

const props: ProductUpdatePageProps = {
  ...listActionsProps,
  categories: [product.category],
  collections,
  disabled: false,
  errors: [],
  fetchCategories: () => undefined,
  fetchCollections: () => undefined,
  header: product.name,
  images: product.images,
  onAttributesEdit: () => undefined,
  onBack: () => undefined,
  onDelete: () => undefined,
  onImageDelete: () => undefined,
  onImageUpload: () => undefined,
  onProductShow: () => undefined,
  onSubmit: () => undefined,
  onVariantAdd: () => undefined,
  onVariantShow: () => undefined,
  placeholderImage,
  product,
  saveButtonBarState: "default",
  variants: product.variants
};

storiesOf("Views / Products / Product edit", module)
  .addDecorator(Decorator)
  .add("when data is fully loaded", () => <ProductUpdatePage {...props} />)
  .add("when product has no images", () => (
    <ProductUpdatePage {...props} images={[]} />
  ))
  .add("when product has no variants", () => (
    <ProductUpdatePage
      {...props}
      product={{
        ...product,
        productType: { ...product.productType, hasVariants: false }
      }}
    />
  ))
  .add("when loading data", () => (
    <ProductUpdatePage
      {...props}
      disabled={true}
      header={undefined}
      categories={[]}
      variants={undefined}
      product={undefined}
      collections={undefined}
      images={undefined}
    />
  ));
