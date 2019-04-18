import { storiesOf } from "@storybook/react";
import * as React from "react";

import * as placeholderImage from "../../../../images/placeholder255x255.png";
import { listActionsProps } from "../../../fixtures";
import ProductUpdatePage from "../../../products/components/ProductUpdatePage";
import { product as productFixture } from "../../../products/fixtures";
import Decorator from "../../Decorator";

const product = productFixture(placeholderImage);

storiesOf("Views / Products / Product edit", module)
  .addDecorator(Decorator)
  .add("when data is fully loaded", () => (
    <ProductUpdatePage
      errors={[]}
      onBack={() => undefined}
      onSubmit={() => undefined}
      product={product}
      header={product.name}
      collections={product.collections}
      categories={[product.category]}
      fetchCategories={() => undefined}
      fetchCollections={() => undefined}
      placeholderImage={placeholderImage}
      images={product.images}
      variants={product.variants}
      productCollections={product.collections}
      onAttributesEdit={undefined}
      onDelete={undefined}
      onProductShow={undefined}
      onVariantAdd={undefined}
      onVariantShow={() => undefined}
      onImageDelete={() => undefined}
      onImageUpload={() => undefined}
      saveButtonBarState="default"
      {...listActionsProps}
    />
  ))
  .add("when product has no images", () => (
    <ProductUpdatePage
      errors={[]}
      onBack={() => undefined}
      onSubmit={() => undefined}
      product={product}
      header={product.name}
      collections={product.collections}
      categories={[product.category]}
      fetchCategories={() => undefined}
      fetchCollections={() => undefined}
      placeholderImage={placeholderImage}
      images={[]}
      variants={product.variants}
      productCollections={product.collections}
      onAttributesEdit={undefined}
      onDelete={undefined}
      onProductShow={undefined}
      onImageDelete={() => undefined}
      onVariantAdd={undefined}
      onVariantShow={() => undefined}
      onImageUpload={() => undefined}
      saveButtonBarState="default"
      {...listActionsProps}
    />
  ))
  .add("when product has no variants", () => (
    <ProductUpdatePage
      errors={[]}
      onBack={() => undefined}
      onSubmit={() => undefined}
      product={
        {
          ...product,
          productType: { ...product.productType, hasVariants: false }
        } as any
      }
      header={product.name}
      collections={product.collections}
      categories={[product.category]}
      fetchCategories={() => undefined}
      fetchCollections={() => undefined}
      placeholderImage={placeholderImage}
      images={product.images}
      variants={product.variants}
      productCollections={product.collections}
      onAttributesEdit={undefined}
      onDelete={undefined}
      onProductShow={undefined}
      onVariantAdd={undefined}
      onImageDelete={() => undefined}
      onVariantShow={() => undefined}
      onImageUpload={() => undefined}
      saveButtonBarState="default"
      {...listActionsProps}
    />
  ))
  .add("when loading data", () => (
    <ProductUpdatePage
      errors={[]}
      header={undefined}
      categories={[]}
      fetchCategories={() => undefined}
      fetchCollections={() => undefined}
      onBack={() => undefined}
      onSubmit={() => undefined}
      disabled={true}
      placeholderImage={placeholderImage}
      onAttributesEdit={undefined}
      onDelete={undefined}
      onImageDelete={() => undefined}
      onVariantShow={() => undefined}
      onImageUpload={() => undefined}
      saveButtonBarState="default"
      variants={undefined}
      {...listActionsProps}
    />
  ));
