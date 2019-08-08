/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: ProductVariantDetails
// ====================================================

export interface ProductVariantDetails_productVariant_attributes_attribute_values {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface ProductVariantDetails_productVariant_attributes_attribute {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
  valueRequired: boolean;
  values: (ProductVariantDetails_productVariant_attributes_attribute_values | null)[] | null;
}

export interface ProductVariantDetails_productVariant_attributes_value {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface ProductVariantDetails_productVariant_attributes {
  __typename: "SelectedAttribute";
  attribute: ProductVariantDetails_productVariant_attributes_attribute;
  value: ProductVariantDetails_productVariant_attributes_value | null;
}

export interface ProductVariantDetails_productVariant_costPrice {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface ProductVariantDetails_productVariant_images {
  __typename: "ProductImage";
  id: string;
  url: string;
}

export interface ProductVariantDetails_productVariant_priceOverride {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface ProductVariantDetails_productVariant_product_images {
  __typename: "ProductImage";
  id: string;
  alt: string;
  sortOrder: number | null;
  url: string;
}

export interface ProductVariantDetails_productVariant_product_thumbnail {
  __typename: "Image";
  url: string;
}

export interface ProductVariantDetails_productVariant_product_variants_images {
  __typename: "ProductImage";
  id: string;
  url: string;
}

export interface ProductVariantDetails_productVariant_product_variants {
  __typename: "ProductVariant";
  id: string;
  name: string;
  sku: string;
  images: (ProductVariantDetails_productVariant_product_variants_images | null)[] | null;
}

export interface ProductVariantDetails_productVariant_product {
  __typename: "Product";
  id: string;
  images: (ProductVariantDetails_productVariant_product_images | null)[] | null;
  name: string;
  thumbnail: ProductVariantDetails_productVariant_product_thumbnail | null;
  variants: (ProductVariantDetails_productVariant_product_variants | null)[] | null;
}

export interface ProductVariantDetails_productVariant {
  __typename: "ProductVariant";
  id: string;
  attributes: ProductVariantDetails_productVariant_attributes[];
  costPrice: ProductVariantDetails_productVariant_costPrice | null;
  images: (ProductVariantDetails_productVariant_images | null)[] | null;
  name: string;
  priceOverride: ProductVariantDetails_productVariant_priceOverride | null;
  product: ProductVariantDetails_productVariant_product;
  sku: string;
  quantity: number;
  quantityAllocated: number;
}

export interface ProductVariantDetails {
  productVariant: ProductVariantDetails_productVariant | null;
}

export interface ProductVariantDetailsVariables {
  id: string;
}
