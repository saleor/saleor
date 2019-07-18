/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: ProductImageUpdate
// ====================================================

export interface ProductImageUpdate_productImageUpdate_errors {
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

export interface ProductImageUpdate_productImageUpdate_product_category {
  __typename: "Category";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface ProductImageUpdate_productImageUpdate_product_collections {
  __typename: "Collection";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface ProductImageUpdate_productImageUpdate_product_basePrice {
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

export interface ProductImageUpdate_productImageUpdate_product_margin {
  __typename: "Margin";
  start: number | null;
  stop: number | null;
}

export interface ProductImageUpdate_productImageUpdate_product_purchaseCost_start {
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

export interface ProductImageUpdate_productImageUpdate_product_purchaseCost_stop {
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

export interface ProductImageUpdate_productImageUpdate_product_purchaseCost {
  __typename: "MoneyRange";
  /**
   * Lower bound of a price range.
   */
  start: ProductImageUpdate_productImageUpdate_product_purchaseCost_start | null;
  /**
   * Upper bound of a price range.
   */
  stop: ProductImageUpdate_productImageUpdate_product_purchaseCost_stop | null;
}

export interface ProductImageUpdate_productImageUpdate_product_attributes_attribute_values {
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

export interface ProductImageUpdate_productImageUpdate_product_attributes_attribute {
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
  values: (ProductImageUpdate_productImageUpdate_product_attributes_attribute_values | null)[] | null;
}

export interface ProductImageUpdate_productImageUpdate_product_attributes_value {
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

export interface ProductImageUpdate_productImageUpdate_product_attributes {
  __typename: "SelectedAttribute";
  /**
   * Name of an attribute displayed in the interface.
   */
  attribute: ProductImageUpdate_productImageUpdate_product_attributes_attribute;
  /**
   * Value of an attribute.
   */
  value: ProductImageUpdate_productImageUpdate_product_attributes_value;
}

export interface ProductImageUpdate_productImageUpdate_product_pricing_priceRange_start_net {
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

export interface ProductImageUpdate_productImageUpdate_product_pricing_priceRange_start {
  __typename: "TaxedMoney";
  /**
   * Amount of money without taxes.
   */
  net: ProductImageUpdate_productImageUpdate_product_pricing_priceRange_start_net;
}

export interface ProductImageUpdate_productImageUpdate_product_pricing_priceRange_stop_net {
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

export interface ProductImageUpdate_productImageUpdate_product_pricing_priceRange_stop {
  __typename: "TaxedMoney";
  /**
   * Amount of money without taxes.
   */
  net: ProductImageUpdate_productImageUpdate_product_pricing_priceRange_stop_net;
}

export interface ProductImageUpdate_productImageUpdate_product_pricing_priceRange {
  __typename: "TaxedMoneyRange";
  /**
   * Lower bound of a price range.
   */
  start: ProductImageUpdate_productImageUpdate_product_pricing_priceRange_start | null;
  /**
   * Upper bound of a price range.
   */
  stop: ProductImageUpdate_productImageUpdate_product_pricing_priceRange_stop | null;
}

export interface ProductImageUpdate_productImageUpdate_product_pricing {
  __typename: "ProductPricingInfo";
  /**
   * The discounted price range of the product variants.
   */
  priceRange: ProductImageUpdate_productImageUpdate_product_pricing_priceRange | null;
}

export interface ProductImageUpdate_productImageUpdate_product_images {
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

export interface ProductImageUpdate_productImageUpdate_product_variants_priceOverride {
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

export interface ProductImageUpdate_productImageUpdate_product_variants {
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
  priceOverride: ProductImageUpdate_productImageUpdate_product_variants_priceOverride | null;
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

export interface ProductImageUpdate_productImageUpdate_product_productType {
  __typename: "ProductType";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  hasVariants: boolean;
}

export interface ProductImageUpdate_productImageUpdate_product {
  __typename: "Product";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  descriptionJson: any;
  seoTitle: string | null;
  seoDescription: string | null;
  category: ProductImageUpdate_productImageUpdate_product_category;
  /**
   * List of collections for the product
   */
  collections: (ProductImageUpdate_productImageUpdate_product_collections | null)[] | null;
  /**
   * The product's default base price.
   */
  basePrice: ProductImageUpdate_productImageUpdate_product_basePrice | null;
  margin: ProductImageUpdate_productImageUpdate_product_margin | null;
  purchaseCost: ProductImageUpdate_productImageUpdate_product_purchaseCost | null;
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
  attributes: ProductImageUpdate_productImageUpdate_product_attributes[];
  /**
   * Lists the storefront product's pricing,
   *             the current price and discounts, only meant for displaying.
   */
  pricing: ProductImageUpdate_productImageUpdate_product_pricing | null;
  /**
   * List of images for the product
   */
  images: (ProductImageUpdate_productImageUpdate_product_images | null)[] | null;
  /**
   * List of variants for the product
   */
  variants: (ProductImageUpdate_productImageUpdate_product_variants | null)[] | null;
  productType: ProductImageUpdate_productImageUpdate_product_productType;
  /**
   * The storefront URL for the product.
   */
  url: string;
}

export interface ProductImageUpdate_productImageUpdate {
  __typename: "ProductImageUpdate";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: ProductImageUpdate_productImageUpdate_errors[] | null;
  product: ProductImageUpdate_productImageUpdate_product | null;
}

export interface ProductImageUpdate {
  /**
   * Updates a product image.
   */
  productImageUpdate: ProductImageUpdate_productImageUpdate | null;
}

export interface ProductImageUpdateVariables {
  id: string;
  alt: string;
}
