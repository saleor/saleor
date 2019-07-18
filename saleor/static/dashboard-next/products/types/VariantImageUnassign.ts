/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: VariantImageUnassign
// ====================================================

export interface VariantImageUnassign_variantImageUnassign_errors {
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

export interface VariantImageUnassign_variantImageUnassign_productVariant_attributes_attribute_values {
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

export interface VariantImageUnassign_variantImageUnassign_productVariant_attributes_attribute {
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
  values: (VariantImageUnassign_variantImageUnassign_productVariant_attributes_attribute_values | null)[] | null;
}

export interface VariantImageUnassign_variantImageUnassign_productVariant_attributes_value {
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

export interface VariantImageUnassign_variantImageUnassign_productVariant_attributes {
  __typename: "SelectedAttribute";
  /**
   * Name of an attribute displayed in the interface.
   */
  attribute: VariantImageUnassign_variantImageUnassign_productVariant_attributes_attribute;
  /**
   * Value of an attribute.
   */
  value: VariantImageUnassign_variantImageUnassign_productVariant_attributes_value;
}

export interface VariantImageUnassign_variantImageUnassign_productVariant_costPrice {
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

export interface VariantImageUnassign_variantImageUnassign_productVariant_images {
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

export interface VariantImageUnassign_variantImageUnassign_productVariant_priceOverride {
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

export interface VariantImageUnassign_variantImageUnassign_productVariant_product_images {
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

export interface VariantImageUnassign_variantImageUnassign_productVariant_product_thumbnail {
  __typename: "Image";
  /**
   * The URL of the image.
   */
  url: string;
}

export interface VariantImageUnassign_variantImageUnassign_productVariant_product_variants_images {
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

export interface VariantImageUnassign_variantImageUnassign_productVariant_product_variants {
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
  images: (VariantImageUnassign_variantImageUnassign_productVariant_product_variants_images | null)[] | null;
}

export interface VariantImageUnassign_variantImageUnassign_productVariant_product {
  __typename: "Product";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * List of images for the product
   */
  images: (VariantImageUnassign_variantImageUnassign_productVariant_product_images | null)[] | null;
  name: string;
  /**
   * The main thumbnail for a product.
   */
  thumbnail: VariantImageUnassign_variantImageUnassign_productVariant_product_thumbnail | null;
  /**
   * List of variants for the product
   */
  variants: (VariantImageUnassign_variantImageUnassign_productVariant_product_variants | null)[] | null;
}

export interface VariantImageUnassign_variantImageUnassign_productVariant {
  __typename: "ProductVariant";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * List of attributes assigned to this variant.
   */
  attributes: VariantImageUnassign_variantImageUnassign_productVariant_attributes[];
  /**
   * Cost price of the variant.
   */
  costPrice: VariantImageUnassign_variantImageUnassign_productVariant_costPrice | null;
  /**
   * List of images for the product variant
   */
  images: (VariantImageUnassign_variantImageUnassign_productVariant_images | null)[] | null;
  name: string;
  /**
   * Override the base price of a product if necessary.
   * A value of `null` indicates that the default product
   * price is used.
   */
  priceOverride: VariantImageUnassign_variantImageUnassign_productVariant_priceOverride | null;
  product: VariantImageUnassign_variantImageUnassign_productVariant_product;
  sku: string;
  quantity: number;
  quantityAllocated: number;
}

export interface VariantImageUnassign_variantImageUnassign {
  __typename: "VariantImageUnassign";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: VariantImageUnassign_variantImageUnassign_errors[] | null;
  productVariant: VariantImageUnassign_variantImageUnassign_productVariant | null;
}

export interface VariantImageUnassign {
  /**
   * Unassign an image from a product variant
   */
  variantImageUnassign: VariantImageUnassign_variantImageUnassign | null;
}

export interface VariantImageUnassignVariables {
  variantId: string;
  imageId: string;
}
