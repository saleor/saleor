/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { AttributeValueInput, ProductVariantInput, SeoInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: SimpleProductUpdate
// ====================================================

export interface SimpleProductUpdate_productUpdate_errors {
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

export interface SimpleProductUpdate_productUpdate_product_category {
  __typename: "Category";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface SimpleProductUpdate_productUpdate_product_collections {
  __typename: "Collection";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface SimpleProductUpdate_productUpdate_product_basePrice {
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

export interface SimpleProductUpdate_productUpdate_product_margin {
  __typename: "Margin";
  start: number | null;
  stop: number | null;
}

export interface SimpleProductUpdate_productUpdate_product_purchaseCost_start {
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

export interface SimpleProductUpdate_productUpdate_product_purchaseCost_stop {
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

export interface SimpleProductUpdate_productUpdate_product_purchaseCost {
  __typename: "MoneyRange";
  /**
   * Lower bound of a price range.
   */
  start: SimpleProductUpdate_productUpdate_product_purchaseCost_start | null;
  /**
   * Upper bound of a price range.
   */
  stop: SimpleProductUpdate_productUpdate_product_purchaseCost_stop | null;
}

export interface SimpleProductUpdate_productUpdate_product_attributes_attribute_values {
  __typename: "AttributeValue";
  /**
   * Name of a value displayed in the interface.
   */
  name: string | null;
  /**
   * Internal representation of a value (unique per attribute).
   */
  slug: string | null;
}

export interface SimpleProductUpdate_productUpdate_product_attributes_attribute {
  __typename: "Attribute";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * Internal representation of an attribute name.
   */
  slug: string | null;
  /**
   * Name of an attribute displayed in the interface.
   */
  name: string | null;
  /**
   * List of attribute's values.
   */
  values: (SimpleProductUpdate_productUpdate_product_attributes_attribute_values | null)[] | null;
}

export interface SimpleProductUpdate_productUpdate_product_attributes_value {
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

export interface SimpleProductUpdate_productUpdate_product_attributes {
  __typename: "SelectedAttribute";
  /**
   * Name of an attribute displayed in the interface.
   */
  attribute: SimpleProductUpdate_productUpdate_product_attributes_attribute;
  /**
   * Value of an attribute.
   */
  value: SimpleProductUpdate_productUpdate_product_attributes_value;
}

export interface SimpleProductUpdate_productUpdate_product_pricing_priceRange_start_net {
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

export interface SimpleProductUpdate_productUpdate_product_pricing_priceRange_start {
  __typename: "TaxedMoney";
  /**
   * Amount of money without taxes.
   */
  net: SimpleProductUpdate_productUpdate_product_pricing_priceRange_start_net;
}

export interface SimpleProductUpdate_productUpdate_product_pricing_priceRange_stop_net {
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

export interface SimpleProductUpdate_productUpdate_product_pricing_priceRange_stop {
  __typename: "TaxedMoney";
  /**
   * Amount of money without taxes.
   */
  net: SimpleProductUpdate_productUpdate_product_pricing_priceRange_stop_net;
}

export interface SimpleProductUpdate_productUpdate_product_pricing_priceRange {
  __typename: "TaxedMoneyRange";
  /**
   * Lower bound of a price range.
   */
  start: SimpleProductUpdate_productUpdate_product_pricing_priceRange_start | null;
  /**
   * Upper bound of a price range.
   */
  stop: SimpleProductUpdate_productUpdate_product_pricing_priceRange_stop | null;
}

export interface SimpleProductUpdate_productUpdate_product_pricing {
  __typename: "ProductPricingInfo";
  /**
   * The discounted price range of the product variants.
   */
  priceRange: SimpleProductUpdate_productUpdate_product_pricing_priceRange | null;
}

export interface SimpleProductUpdate_productUpdate_product_images {
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

export interface SimpleProductUpdate_productUpdate_product_variants_priceOverride {
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

export interface SimpleProductUpdate_productUpdate_product_variants {
  __typename: "ProductVariant";
  /**
   * The ID of the object.
   */
  id: string;
  sku: string;
  name: string;
  /**
   * Override the base price of a product if necessary.
   * A value of `null` indicates that the default product
   * price is used.
   */
  priceOverride: SimpleProductUpdate_productUpdate_product_variants_priceOverride | null;
  /**
   * Gross margin percentage value.
   */
  margin: number | null;
  quantity: number;
  quantityAllocated: number;
  /**
   * Quantity of a product available for sale.
   */
  stockQuantity: number;
}

export interface SimpleProductUpdate_productUpdate_product_productType {
  __typename: "ProductType";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  hasVariants: boolean;
}

export interface SimpleProductUpdate_productUpdate_product {
  __typename: "Product";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  descriptionJson: any;
  seoTitle: string | null;
  seoDescription: string | null;
  category: SimpleProductUpdate_productUpdate_product_category;
  /**
   * List of collections for the product
   */
  collections: (SimpleProductUpdate_productUpdate_product_collections | null)[] | null;
  /**
   * The product's default base price.
   */
  basePrice: SimpleProductUpdate_productUpdate_product_basePrice | null;
  margin: SimpleProductUpdate_productUpdate_product_margin | null;
  purchaseCost: SimpleProductUpdate_productUpdate_product_purchaseCost | null;
  /**
   * Whether the product is in stock and visible or not.
   */
  isAvailable: boolean | null;
  isPublished: boolean;
  chargeTaxes: boolean;
  publicationDate: any | null;
  /**
   * List of attributes assigned to this product.
   */
  attributes: SimpleProductUpdate_productUpdate_product_attributes[];
  /**
   * Lists the storefront product's pricing,
   *             the current price and discounts, only meant for displaying.
   */
  pricing: SimpleProductUpdate_productUpdate_product_pricing | null;
  /**
   * List of images for the product
   */
  images: (SimpleProductUpdate_productUpdate_product_images | null)[] | null;
  /**
   * List of variants for the product
   */
  variants: (SimpleProductUpdate_productUpdate_product_variants | null)[] | null;
  productType: SimpleProductUpdate_productUpdate_product_productType;
  /**
   * The storefront URL for the product.
   */
  url: string;
}

export interface SimpleProductUpdate_productUpdate {
  __typename: "ProductUpdate";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: SimpleProductUpdate_productUpdate_errors[] | null;
  product: SimpleProductUpdate_productUpdate_product | null;
}

export interface SimpleProductUpdate_productVariantUpdate_errors {
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

export interface SimpleProductUpdate_productVariantUpdate_productVariant_attributes_attribute_values {
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

export interface SimpleProductUpdate_productVariantUpdate_productVariant_attributes_attribute {
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
  values: (SimpleProductUpdate_productVariantUpdate_productVariant_attributes_attribute_values | null)[] | null;
}

export interface SimpleProductUpdate_productVariantUpdate_productVariant_attributes_value {
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

export interface SimpleProductUpdate_productVariantUpdate_productVariant_attributes {
  __typename: "SelectedAttribute";
  /**
   * Name of an attribute displayed in the interface.
   */
  attribute: SimpleProductUpdate_productVariantUpdate_productVariant_attributes_attribute;
  /**
   * Value of an attribute.
   */
  value: SimpleProductUpdate_productVariantUpdate_productVariant_attributes_value;
}

export interface SimpleProductUpdate_productVariantUpdate_productVariant_costPrice {
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

export interface SimpleProductUpdate_productVariantUpdate_productVariant_images {
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

export interface SimpleProductUpdate_productVariantUpdate_productVariant_priceOverride {
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

export interface SimpleProductUpdate_productVariantUpdate_productVariant_product_images {
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

export interface SimpleProductUpdate_productVariantUpdate_productVariant_product_thumbnail {
  __typename: "Image";
  /**
   * The URL of the image.
   */
  url: string;
}

export interface SimpleProductUpdate_productVariantUpdate_productVariant_product_variants_images {
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

export interface SimpleProductUpdate_productVariantUpdate_productVariant_product_variants {
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
  images: (SimpleProductUpdate_productVariantUpdate_productVariant_product_variants_images | null)[] | null;
}

export interface SimpleProductUpdate_productVariantUpdate_productVariant_product {
  __typename: "Product";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * List of images for the product
   */
  images: (SimpleProductUpdate_productVariantUpdate_productVariant_product_images | null)[] | null;
  name: string;
  /**
   * The main thumbnail for a product.
   */
  thumbnail: SimpleProductUpdate_productVariantUpdate_productVariant_product_thumbnail | null;
  /**
   * List of variants for the product
   */
  variants: (SimpleProductUpdate_productVariantUpdate_productVariant_product_variants | null)[] | null;
}

export interface SimpleProductUpdate_productVariantUpdate_productVariant {
  __typename: "ProductVariant";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * List of attributes assigned to this variant.
   */
  attributes: SimpleProductUpdate_productVariantUpdate_productVariant_attributes[];
  /**
   * Cost price of the variant.
   */
  costPrice: SimpleProductUpdate_productVariantUpdate_productVariant_costPrice | null;
  /**
   * List of images for the product variant
   */
  images: (SimpleProductUpdate_productVariantUpdate_productVariant_images | null)[] | null;
  name: string;
  /**
   * Override the base price of a product if necessary.
   * A value of `null` indicates that the default product
   * price is used.
   */
  priceOverride: SimpleProductUpdate_productVariantUpdate_productVariant_priceOverride | null;
  product: SimpleProductUpdate_productVariantUpdate_productVariant_product;
  sku: string;
  quantity: number;
  quantityAllocated: number;
}

export interface SimpleProductUpdate_productVariantUpdate {
  __typename: "ProductVariantUpdate";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: SimpleProductUpdate_productVariantUpdate_errors[] | null;
  productVariant: SimpleProductUpdate_productVariantUpdate_productVariant | null;
}

export interface SimpleProductUpdate {
  /**
   * Updates an existing product.
   */
  productUpdate: SimpleProductUpdate_productUpdate | null;
  /**
   * Updates an existing variant for product
   */
  productVariantUpdate: SimpleProductUpdate_productVariantUpdate | null;
}

export interface SimpleProductUpdateVariables {
  id: string;
  attributes?: (AttributeValueInput | null)[] | null;
  publicationDate?: any | null;
  category?: string | null;
  chargeTaxes: boolean;
  collections?: (string | null)[] | null;
  descriptionJson?: any | null;
  isPublished: boolean;
  name?: string | null;
  basePrice?: any | null;
  productVariantId: string;
  productVariantInput: ProductVariantInput;
  seo?: SeoInput | null;
}
