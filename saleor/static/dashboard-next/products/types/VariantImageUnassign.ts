/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: VariantImageUnassign
// ====================================================

export interface VariantImageUnassign_variantImageUnassign_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface VariantImageUnassign_variantImageUnassign_productVariant_attributes_attribute_values {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface VariantImageUnassign_variantImageUnassign_productVariant_attributes_attribute {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
  valueRequired: boolean;
  values: (VariantImageUnassign_variantImageUnassign_productVariant_attributes_attribute_values | null)[] | null;
}

export interface VariantImageUnassign_variantImageUnassign_productVariant_attributes_value {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface VariantImageUnassign_variantImageUnassign_productVariant_attributes {
  __typename: "SelectedAttribute";
  attribute: VariantImageUnassign_variantImageUnassign_productVariant_attributes_attribute;
  value: VariantImageUnassign_variantImageUnassign_productVariant_attributes_value | null;
}

export interface VariantImageUnassign_variantImageUnassign_productVariant_costPrice {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface VariantImageUnassign_variantImageUnassign_productVariant_images {
  __typename: "ProductImage";
  id: string;
  url: string;
}

export interface VariantImageUnassign_variantImageUnassign_productVariant_priceOverride {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface VariantImageUnassign_variantImageUnassign_productVariant_product_images {
  __typename: "ProductImage";
  id: string;
  alt: string;
  sortOrder: number | null;
  url: string;
}

export interface VariantImageUnassign_variantImageUnassign_productVariant_product_thumbnail {
  __typename: "Image";
  url: string;
}

export interface VariantImageUnassign_variantImageUnassign_productVariant_product_variants_images {
  __typename: "ProductImage";
  id: string;
  url: string;
}

export interface VariantImageUnassign_variantImageUnassign_productVariant_product_variants {
  __typename: "ProductVariant";
  id: string;
  name: string;
  sku: string;
  images: (VariantImageUnassign_variantImageUnassign_productVariant_product_variants_images | null)[] | null;
}

export interface VariantImageUnassign_variantImageUnassign_productVariant_product {
  __typename: "Product";
  id: string;
  images: (VariantImageUnassign_variantImageUnassign_productVariant_product_images | null)[] | null;
  name: string;
  thumbnail: VariantImageUnassign_variantImageUnassign_productVariant_product_thumbnail | null;
  variants: (VariantImageUnassign_variantImageUnassign_productVariant_product_variants | null)[] | null;
}

export interface VariantImageUnassign_variantImageUnassign_productVariant {
  __typename: "ProductVariant";
  id: string;
  attributes: VariantImageUnassign_variantImageUnassign_productVariant_attributes[];
  costPrice: VariantImageUnassign_variantImageUnassign_productVariant_costPrice | null;
  images: (VariantImageUnassign_variantImageUnassign_productVariant_images | null)[] | null;
  name: string;
  priceOverride: VariantImageUnassign_variantImageUnassign_productVariant_priceOverride | null;
  product: VariantImageUnassign_variantImageUnassign_productVariant_product;
  sku: string;
  quantity: number;
  quantityAllocated: number;
}

export interface VariantImageUnassign_variantImageUnassign {
  __typename: "VariantImageUnassign";
  errors: VariantImageUnassign_variantImageUnassign_errors[] | null;
  productVariant: VariantImageUnassign_variantImageUnassign_productVariant | null;
}

export interface VariantImageUnassign {
  variantImageUnassign: VariantImageUnassign_variantImageUnassign | null;
}

export interface VariantImageUnassignVariables {
  variantId: string;
  imageId: string;
}
