/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: Product
// ====================================================

export interface Product_category {
  __typename: "Category";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface Product_collections {
  __typename: "Collection";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface Product_basePrice {
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

export interface Product_margin {
  __typename: "Margin";
  start: number | null;
  stop: number | null;
}

export interface Product_purchaseCost_start {
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

export interface Product_purchaseCost_stop {
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

export interface Product_purchaseCost {
  __typename: "MoneyRange";
  /**
   * Lower bound of a price range.
   */
  start: Product_purchaseCost_start | null;
  /**
   * Upper bound of a price range.
   */
  stop: Product_purchaseCost_stop | null;
}

export interface Product_attributes_attribute_values {
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

export interface Product_attributes_attribute {
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
  values: (Product_attributes_attribute_values | null)[] | null;
}

export interface Product_attributes_value {
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

export interface Product_attributes {
  __typename: "SelectedAttribute";
  /**
   * Name of an attribute displayed in the interface.
   */
  attribute: Product_attributes_attribute;
  /**
   * Value of an attribute.
   */
  value: Product_attributes_value;
}

export interface Product_pricing_priceRange_start_net {
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

export interface Product_pricing_priceRange_start {
  __typename: "TaxedMoney";
  /**
   * Amount of money without taxes.
   */
  net: Product_pricing_priceRange_start_net;
}

export interface Product_pricing_priceRange_stop_net {
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

export interface Product_pricing_priceRange_stop {
  __typename: "TaxedMoney";
  /**
   * Amount of money without taxes.
   */
  net: Product_pricing_priceRange_stop_net;
}

export interface Product_pricing_priceRange {
  __typename: "TaxedMoneyRange";
  /**
   * Lower bound of a price range.
   */
  start: Product_pricing_priceRange_start | null;
  /**
   * Upper bound of a price range.
   */
  stop: Product_pricing_priceRange_stop | null;
}

export interface Product_pricing {
  __typename: "ProductPricingInfo";
  /**
   * The discounted price range of the product variants.
   */
  priceRange: Product_pricing_priceRange | null;
}

export interface Product_images {
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

export interface Product_variants_priceOverride {
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

export interface Product_variants {
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
  priceOverride: Product_variants_priceOverride | null;
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

export interface Product_productType {
  __typename: "ProductType";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  hasVariants: boolean;
}

export interface Product {
  __typename: "Product";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  descriptionJson: any;
  seoTitle: string | null;
  seoDescription: string | null;
  category: Product_category;
  /**
   * List of collections for the product
   */
  collections: (Product_collections | null)[] | null;
  /**
   * The product's default base price.
   */
  basePrice: Product_basePrice | null;
  margin: Product_margin | null;
  purchaseCost: Product_purchaseCost | null;
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
  attributes: Product_attributes[];
  /**
   * Lists the storefront product's pricing,
   *             the current price and discounts, only meant for displaying.
   */
  pricing: Product_pricing | null;
  /**
   * List of images for the product
   */
  images: (Product_images | null)[] | null;
  /**
   * List of variants for the product
   */
  variants: (Product_variants | null)[] | null;
  productType: Product_productType;
  /**
   * The storefront URL for the product.
   */
  url: string;
}
