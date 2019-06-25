import { storiesOf } from "@storybook/react";
import React from "react";

import { collections } from "@saleor/collections/fixtures";
import { listActionsProps } from "@saleor/fixtures";
import ProductUpdatePage from "@saleor/products/components/ProductUpdatePage";
import { product as productFixture } from "@saleor/products/fixtures";
import placeholderImage from "../../../../images/placeholder255x255.png";
import Decorator from "../../Decorator";

const product = productFixture(placeholderImage);

storiesOf("Views / Products / Product edit", module)
  .addDecorator(Decorator)
  .add("when data is fully loaded", () => (
    <ProductUpdatePage
      disabled={false}
      errors={[]}
      onBack={() => undefined}
      onSubmit={() => undefined}
      product={product}
      header={product.name}
      collections={collections}
      categories={[product.category]}
      fetchCategories={() => undefined}
      fetchCollections={undefined}
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
      disabled={false}
      errors={[]}
      onBack={() => undefined}
      onSubmit={() => undefined}
      product={product}
      header={product.name}
      collections={collections}
      categories={[product.category]}
      fetchCategories={() => undefined}
      fetchCollections={undefined}
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
      disabled={false}
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
      collections={collections}
      categories={[product.category]}
      fetchCategories={() => undefined}
      fetchCollections={undefined}
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
      fetchCollections={undefined}
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
      product={undefined}
      collections={undefined}
      images={undefined}
      productCollections={undefined}
      {...listActionsProps}
    />
  ));
