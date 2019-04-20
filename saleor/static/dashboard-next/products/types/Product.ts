/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: Product
// ====================================================

export interface Product_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface Product_collections {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface Product_price {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface Product_margin {
  __typename: "Margin";
  start: number | null;
  stop: number | null;
}

export interface Product_purchaseCost_start {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface Product_purchaseCost_stop {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface Product_purchaseCost {
  __typename: "MoneyRange";
  start: Product_purchaseCost_start | null;
  stop: Product_purchaseCost_stop | null;
}

export interface Product_attributes_attribute_values {
  __typename: "AttributeValue";
  name: string | null;
  slug: string | null;
}

export interface Product_attributes_attribute {
  __typename: "Attribute";
  id: string;
  slug: string | null;
  name: string | null;
  values: (Product_attributes_attribute_values | null)[] | null;
}

export interface Product_attributes_value {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface Product_attributes {
  __typename: "SelectedAttribute";
  attribute: Product_attributes_attribute;
  value: Product_attributes_value;
}

export interface Product_availability_priceRange_start_net {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface Product_availability_priceRange_start {
  __typename: "TaxedMoney";
  net: Product_availability_priceRange_start_net;
}

export interface Product_availability_priceRange_stop_net {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface Product_availability_priceRange_stop {
  __typename: "TaxedMoney";
  net: Product_availability_priceRange_stop_net;
}

export interface Product_availability_priceRange {
  __typename: "TaxedMoneyRange";
  start: Product_availability_priceRange_start | null;
  stop: Product_availability_priceRange_stop | null;
}

export interface Product_availability {
  __typename: "ProductAvailability";
  available: boolean | null;
  priceRange: Product_availability_priceRange | null;
}

export interface Product_images {
  __typename: "ProductImage";
  id: string;
  alt: string;
  sortOrder: number;
  url: string;
}

export interface Product_variants_priceOverride {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface Product_variants {
  __typename: "ProductVariant";
  id: string;
  sku: string;
  name: string;
  priceOverride: Product_variants_priceOverride | null;
  margin: number | null;
  quantity: number;
  quantityAllocated: number;
  stockQuantity: number;
}

export interface Product_productType {
  __typename: "ProductType";
  id: string;
  name: string;
  hasVariants: boolean;
}

export interface Product {
  __typename: "Product";
  id: string;
  name: string;
  descriptionJson: any;
  seoTitle: string | null;
  seoDescription: string | null;
  category: Product_category;
  collections: (Product_collections | null)[] | null;
  price: Product_price | null;
  margin: Product_margin | null;
  purchaseCost: Product_purchaseCost | null;
  isPublished: boolean;
  chargeTaxes: boolean;
  publicationDate: any | null;
  attributes: Product_attributes[];
  availability: Product_availability | null;
  images: (Product_images | null)[] | null;
  variants: (Product_variants | null)[] | null;
  productType: Product_productType;
  url: string;
}
