/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { AttributeValueInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: VariantCreate
// ====================================================

export interface VariantCreate_productVariantCreate_errors {
  __typename: "Error";
  /**
   * Name of a field that caused the error. A value of
   *         `null` indicates that the error isn't associated with a particular
   *         field.
   */
  field: string | null;
  /**
   * The error message.
   */
  message: string | null;
}

export interface VariantCreate_productVariantCreate_productVariant_attributes_attribute_values {
  __typename: "AttributeValue";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * Name of a value displayed in the interface.
   */
  name: string | null;
  /**
   * Internal representation of a value (unique per attribute).
   */
  slug: string | null;
}

export interface VariantCreate_productVariantCreate_productVariant_attributes_attribute {
  __typename: "Attribute";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * Name of an attribute displayed in the interface.
   */
  name: string | null;
  /**
   * Internal representation of an attribute name.
   */
  slug: string | null;
  /**
   * List of attribute's values.
   */
  values: (VariantCreate_productVariantCreate_productVariant_attributes_attribute_values | null)[] | null;
}

export interface VariantCreate_productVariantCreate_productVariant_attributes_value {
  __typename: "AttributeValue";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * Name of a value displayed in the interface.
   */
  name: string | null;
  /**
   * Internal representation of a value (unique per attribute).
   */
  slug: string | null;
}

export interface VariantCreate_productVariantCreate_productVariant_attributes {
  __typename: "SelectedAttribute";
  /**
   * Name of an attribute displayed in the interface.
   */
  attribute: VariantCreate_productVariantCreate_productVariant_attributes_attribute;
  /**
   * Value of an attribute.
   */
  value: VariantCreate_productVariantCreate_productVariant_attributes_value;
}

export interface VariantCreate_productVariantCreate_productVariant_costPrice {
  __typename: "Money";
  /**
   * Amount of money.
   */
  amount: number;
  /**
   * Currency code.
   */
  currency: string;
}

export interface VariantCreate_productVariantCreate_productVariant_images {
  __typename: "ProductImage";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * The URL of the image.
   */
  url: string;
}

export interface VariantCreate_productVariantCreate_productVariant_priceOverride {
  __typename: "Money";
  /**
   * Amount of money.
   */
  amount: number;
  /**
   * Currency code.
   */
  currency: string;
}

export interface VariantCreate_productVariantCreate_productVariant_product_images {
  __typename: "ProductImage";
  /**
   * The ID of the object.
   */
  id: string;
  alt: string;
  sortOrder: number | null;
  /**
   * The URL of the image.
   */
  url: string;
}

export interface VariantCreate_productVariantCreate_productVariant_product_thumbnail {
  __typename: "Image";
  /**
   * The URL of the image.
   */
  url: string;
}

export interface VariantCreate_productVariantCreate_productVariant_product_variants_images {
  __typename: "ProductImage";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * The URL of the image.
   */
  url: string;
}

export interface VariantCreate_productVariantCreate_productVariant_product_variants {
  __typename: "ProductVariant";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  sku: string;
  /**
   * List of images for the product variant
   */
  images: (VariantCreate_productVariantCreate_productVariant_product_variants_images | null)[] | null;
}

export interface VariantCreate_productVariantCreate_productVariant_product {
  __typename: "Product";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * List of images for the product
   */
  images: (VariantCreate_productVariantCreate_productVariant_product_images | null)[] | null;
  name: string;
  /**
   * The main thumbnail for a product.
   */
  thumbnail: VariantCreate_productVariantCreate_productVariant_product_thumbnail | null;
  /**
   * List of variants for the product
   */
  variants: (VariantCreate_productVariantCreate_productVariant_product_variants | null)[] | null;
}

export interface VariantCreate_productVariantCreate_productVariant {
  __typename: "ProductVariant";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * List of attributes assigned to this variant.
   */
  attributes: VariantCreate_productVariantCreate_productVariant_attributes[];
  /**
   * Cost price of the variant.
   */
  costPrice: VariantCreate_productVariantCreate_productVariant_costPrice | null;
  /**
   * List of images for the product variant
   */
  images: (VariantCreate_productVariantCreate_productVariant_images | null)[] | null;
  name: string;
  /**
   * Override the base price of a product if necessary.
   * A value of `null` indicates that the default product
   * price is used.
   */
  priceOverride: VariantCreate_productVariantCreate_productVariant_priceOverride | null;
  product: VariantCreate_productVariantCreate_productVariant_product;
  sku: string;
  quantity: number;
  quantityAllocated: number;
}

export interface VariantCreate_productVariantCreate {
  __typename: "ProductVariantCreate";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: VariantCreate_productVariantCreate_errors[] | null;
  productVariant: VariantCreate_productVariantCreate_productVariant | null;
}

export interface VariantCreate {
  /**
   * Creates a new variant for a product
   */
  productVariantCreate: VariantCreate_productVariantCreate | null;
}

export interface VariantCreateVariables {
  attributes: (AttributeValueInput | null)[];
  costPrice?: any | null;
  priceOverride?: any | null;
  product: string;
  sku?: string | null;
  quantity?: number | null;
  trackInventory: boolean;
}
