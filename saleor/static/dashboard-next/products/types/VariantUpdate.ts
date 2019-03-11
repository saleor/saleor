/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { AttributeValueInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: VariantUpdate
// ====================================================

export interface VariantUpdate_productVariantUpdate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface VariantUpdate_productVariantUpdate_productVariant_attributes_attribute_values {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface VariantUpdate_productVariantUpdate_productVariant_attributes_attribute {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
  values: (VariantUpdate_productVariantUpdate_productVariant_attributes_attribute_values | null)[] | null;
}

export interface VariantUpdate_productVariantUpdate_productVariant_attributes_value {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface VariantUpdate_productVariantUpdate_productVariant_attributes {
  __typename: "SelectedAttribute";
  attribute: VariantUpdate_productVariantUpdate_productVariant_attributes_attribute;
  value: VariantUpdate_productVariantUpdate_productVariant_attributes_value;
}

export interface VariantUpdate_productVariantUpdate_productVariant_costPrice {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface VariantUpdate_productVariantUpdate_productVariant_images {
  __typename: "ProductImage";
  id: string;
  url: string;
}

export interface VariantUpdate_productVariantUpdate_productVariant_priceOverride {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface VariantUpdate_productVariantUpdate_productVariant_product_images {
  __typename: "ProductImage";
  id: string;
  alt: string;
  sortOrder: number;
  url: string;
}

export interface VariantUpdate_productVariantUpdate_productVariant_product_thumbnail {
  __typename: "Image";
  url: string;
}

export interface VariantUpdate_productVariantUpdate_productVariant_product_variants_images {
  __typename: "ProductImage";
  id: string;
  url: string;
}

export interface VariantUpdate_productVariantUpdate_productVariant_product_variants {
  __typename: "ProductVariant";
  id: string;
  name: string;
  sku: string;
  images: (VariantUpdate_productVariantUpdate_productVariant_product_variants_images | null)[] | null;
}

export interface VariantUpdate_productVariantUpdate_productVariant_product {
  __typename: "Product";
  id: string;
  images: (VariantUpdate_productVariantUpdate_productVariant_product_images | null)[] | null;
  name: string;
  thumbnail: VariantUpdate_productVariantUpdate_productVariant_product_thumbnail | null;
  variants: (VariantUpdate_productVariantUpdate_productVariant_product_variants | null)[] | null;
}

export interface VariantUpdate_productVariantUpdate_productVariant {
  __typename: "ProductVariant";
  id: string;
  attributes: VariantUpdate_productVariantUpdate_productVariant_attributes[];
  costPrice: VariantUpdate_productVariantUpdate_productVariant_costPrice | null;
  images: (VariantUpdate_productVariantUpdate_productVariant_images | null)[] | null;
  name: string;
  priceOverride: VariantUpdate_productVariantUpdate_productVariant_priceOverride | null;
  product: VariantUpdate_productVariantUpdate_productVariant_product;
  sku: string;
  quantity: number;
  quantityAllocated: number;
}

export interface VariantUpdate_productVariantUpdate {
  __typename: "ProductVariantUpdate";
  errors: VariantUpdate_productVariantUpdate_errors[] | null;
  productVariant: VariantUpdate_productVariantUpdate_productVariant | null;
}

export interface VariantUpdate {
  productVariantUpdate: VariantUpdate_productVariantUpdate | null;
}

export interface VariantUpdateVariables {
  id: string;
  attributes?: (AttributeValueInput | null)[] | null;
  costPrice?: any | null;
  priceOverride?: any | null;
  sku?: string | null;
  quantity?: number | null;
  trackInventory: boolean;
}
