/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ProductVariant
// ====================================================

export interface ProductVariant_attributes_attribute_values {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface ProductVariant_attributes_attribute {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
  valueRequired: boolean;
  values: (ProductVariant_attributes_attribute_values | null)[] | null;
}

export interface ProductVariant_attributes_value {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface ProductVariant_attributes {
  __typename: "SelectedAttribute";
  attribute: ProductVariant_attributes_attribute;
  value: ProductVariant_attributes_value | null;
}

export interface ProductVariant_costPrice {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface ProductVariant_images {
  __typename: "ProductImage";
  id: string;
  url: string;
}

export interface ProductVariant_priceOverride {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface ProductVariant_product_images {
  __typename: "ProductImage";
  id: string;
  alt: string;
  sortOrder: number | null;
  url: string;
}

export interface ProductVariant_product_thumbnail {
  __typename: "Image";
  url: string;
}

export interface ProductVariant_product_variants_images {
  __typename: "ProductImage";
  id: string;
  url: string;
}

export interface ProductVariant_product_variants {
  __typename: "ProductVariant";
  id: string;
  name: string;
  sku: string;
  images: (ProductVariant_product_variants_images | null)[] | null;
}

export interface ProductVariant_product {
  __typename: "Product";
  id: string;
  images: (ProductVariant_product_images | null)[] | null;
  name: string;
  thumbnail: ProductVariant_product_thumbnail | null;
  variants: (ProductVariant_product_variants | null)[] | null;
}

export interface ProductVariant {
  __typename: "ProductVariant";
  id: string;
  attributes: ProductVariant_attributes[];
  costPrice: ProductVariant_costPrice | null;
  images: (ProductVariant_images | null)[] | null;
  name: string;
  priceOverride: ProductVariant_priceOverride | null;
  product: ProductVariant_product;
  sku: string;
  quantity: number;
  quantityAllocated: number;
}
