/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { AttributeValueInput, SeoInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: ProductCreate
// ====================================================

export interface ProductCreate_productCreate_errors {
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

export interface ProductCreate_productCreate_product_category {
  __typename: "Category";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface ProductCreate_productCreate_product_collections {
  __typename: "Collection";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface ProductCreate_productCreate_product_basePrice {
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

export interface ProductCreate_productCreate_product_margin {
  __typename: "Margin";
  start: number | null;
  stop: number | null;
}

export interface ProductCreate_productCreate_product_purchaseCost_start {
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

export interface ProductCreate_productCreate_product_purchaseCost_stop {
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

export interface ProductCreate_productCreate_product_purchaseCost {
  __typename: "MoneyRange";
  /**
   * Lower bound of a price range.
   */
  start: ProductCreate_productCreate_product_purchaseCost_start | null;
  /**
   * Upper bound of a price range.
   */
  stop: ProductCreate_productCreate_product_purchaseCost_stop | null;
}

export interface ProductCreate_productCreate_product_attributes_attribute_values {
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

export interface ProductCreate_productCreate_product_attributes_attribute {
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
  values: (ProductCreate_productCreate_product_attributes_attribute_values | null)[] | null;
}

export interface ProductCreate_productCreate_product_attributes_value {
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

export interface ProductCreate_productCreate_product_attributes {
  __typename: "SelectedAttribute";
  /**
   * Name of an attribute displayed in the interface.
   */
  attribute: ProductCreate_productCreate_product_attributes_attribute;
  /**
   * Value of an attribute.
   */
  value: ProductCreate_productCreate_product_attributes_value;
}

export interface ProductCreate_productCreate_product_pricing_priceRange_start_net {
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

export interface ProductCreate_productCreate_product_pricing_priceRange_start {
  __typename: "TaxedMoney";
  /**
   * Amount of money without taxes.
   */
  net: ProductCreate_productCreate_product_pricing_priceRange_start_net;
}

export interface ProductCreate_productCreate_product_pricing_priceRange_stop_net {
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

export interface ProductCreate_productCreate_product_pricing_priceRange_stop {
  __typename: "TaxedMoney";
  /**
   * Amount of money without taxes.
   */
  net: ProductCreate_productCreate_product_pricing_priceRange_stop_net;
}

export interface ProductCreate_productCreate_product_pricing_priceRange {
  __typename: "TaxedMoneyRange";
  /**
   * Lower bound of a price range.
   */
  start: ProductCreate_productCreate_product_pricing_priceRange_start | null;
  /**
   * Upper bound of a price range.
   */
  stop: ProductCreate_productCreate_product_pricing_priceRange_stop | null;
}

export interface ProductCreate_productCreate_product_pricing {
  __typename: "ProductPricingInfo";
  /**
   * The discounted price range of the product variants.
   */
  priceRange: ProductCreate_productCreate_product_pricing_priceRange | null;
}

export interface ProductCreate_productCreate_product_images {
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

export interface ProductCreate_productCreate_product_variants_priceOverride {
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

export interface ProductCreate_productCreate_product_variants {
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
  priceOverride: ProductCreate_productCreate_product_variants_priceOverride | null;
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

export interface ProductCreate_productCreate_product_productType {
  __typename: "ProductType";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  hasVariants: boolean;
}

export interface ProductCreate_productCreate_product {
  __typename: "Product";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  descriptionJson: any;
  seoTitle: string | null;
  seoDescription: string | null;
  category: ProductCreate_productCreate_product_category;
  /**
   * List of collections for the product
   */
  collections: (ProductCreate_productCreate_product_collections | null)[] | null;
  /**
   * The product's default base price.
   */
  basePrice: ProductCreate_productCreate_product_basePrice | null;
  margin: ProductCreate_productCreate_product_margin | null;
  purchaseCost: ProductCreate_productCreate_product_purchaseCost | null;
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
  attributes: ProductCreate_productCreate_product_attributes[];
  /**
   * Lists the storefront product's pricing,
   *             the current price and discounts, only meant for displaying.
   */
  pricing: ProductCreate_productCreate_product_pricing | null;
  /**
   * List of images for the product
   */
  images: (ProductCreate_productCreate_product_images | null)[] | null;
  /**
   * List of variants for the product
   */
  variants: (ProductCreate_productCreate_product_variants | null)[] | null;
  productType: ProductCreate_productCreate_product_productType;
  /**
   * The storefront URL for the product.
   */
  url: string;
}

export interface ProductCreate_productCreate {
  __typename: "ProductCreate";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: ProductCreate_productCreate_errors[] | null;
  product: ProductCreate_productCreate_product | null;
}

export interface ProductCreate {
  /**
   * Creates a new product.
   */
  productCreate: ProductCreate_productCreate | null;
}

export interface ProductCreateVariables {
  attributes?: (AttributeValueInput | null)[] | null;
  publicationDate?: any | null;
  category: string;
  chargeTaxes: boolean;
  collections?: (string | null)[] | null;
  descriptionJson?: any | null;
  isPublished: boolean;
  name: string;
  basePrice?: any | null;
  productType: string;
  sku?: string | null;
  stockQuantity?: number | null;
  seo?: SeoInput | null;
}
