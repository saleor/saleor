/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { AttributeValueInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: ProductCreate
// ====================================================

export interface ProductCreate_productCreate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface ProductCreate_productCreate_product_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface ProductCreate_productCreate_product_collections {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface ProductCreate_productCreate_product_price {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface ProductCreate_productCreate_product_margin {
  __typename: "Margin";
  start: number | null;
  stop: number | null;
}

export interface ProductCreate_productCreate_product_purchaseCost_start {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface ProductCreate_productCreate_product_purchaseCost_stop {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface ProductCreate_productCreate_product_purchaseCost {
  __typename: "MoneyRange";
  start: ProductCreate_productCreate_product_purchaseCost_start | null;
  stop: ProductCreate_productCreate_product_purchaseCost_stop | null;
}

export interface ProductCreate_productCreate_product_attributes_attribute_values {
  __typename: "AttributeValue";
  name: string | null;
  slug: string | null;
}

export interface ProductCreate_productCreate_product_attributes_attribute {
  __typename: "Attribute";
  id: string;
  slug: string | null;
  name: string | null;
  values: (ProductCreate_productCreate_product_attributes_attribute_values | null)[] | null;
}

export interface ProductCreate_productCreate_product_attributes_value {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface ProductCreate_productCreate_product_attributes {
  __typename: "SelectedAttribute";
  attribute: ProductCreate_productCreate_product_attributes_attribute;
  value: ProductCreate_productCreate_product_attributes_value;
}

export interface ProductCreate_productCreate_product_availability_priceRange_start_net {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface ProductCreate_productCreate_product_availability_priceRange_start {
  __typename: "TaxedMoney";
  net: ProductCreate_productCreate_product_availability_priceRange_start_net;
}

export interface ProductCreate_productCreate_product_availability_priceRange_stop_net {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface ProductCreate_productCreate_product_availability_priceRange_stop {
  __typename: "TaxedMoney";
  net: ProductCreate_productCreate_product_availability_priceRange_stop_net;
}

export interface ProductCreate_productCreate_product_availability_priceRange {
  __typename: "TaxedMoneyRange";
  start: ProductCreate_productCreate_product_availability_priceRange_start | null;
  stop: ProductCreate_productCreate_product_availability_priceRange_stop | null;
}

export interface ProductCreate_productCreate_product_availability {
  __typename: "ProductAvailability";
  available: boolean | null;
  priceRange: ProductCreate_productCreate_product_availability_priceRange | null;
}

export interface ProductCreate_productCreate_product_images {
  __typename: "ProductImage";
  id: string;
  alt: string;
  sortOrder: number;
  url: string;
}

export interface ProductCreate_productCreate_product_variants_priceOverride {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface ProductCreate_productCreate_product_variants {
  __typename: "ProductVariant";
  id: string;
  sku: string;
  name: string;
  priceOverride: ProductCreate_productCreate_product_variants_priceOverride | null;
  margin: number | null;
  quantity: number;
  quantityAllocated: number;
  stockQuantity: number;
}

export interface ProductCreate_productCreate_product_productType {
  __typename: "ProductType";
  id: string;
  name: string;
  hasVariants: boolean;
}

export interface ProductCreate_productCreate_product {
  __typename: "Product";
  id: string;
  name: string;
  descriptionJson: any;
  seoTitle: string | null;
  seoDescription: string | null;
  category: ProductCreate_productCreate_product_category;
  collections: (ProductCreate_productCreate_product_collections | null)[] | null;
  price: ProductCreate_productCreate_product_price | null;
  margin: ProductCreate_productCreate_product_margin | null;
  purchaseCost: ProductCreate_productCreate_product_purchaseCost | null;
  isPublished: boolean;
  chargeTaxes: boolean;
  publicationDate: any | null;
  attributes: ProductCreate_productCreate_product_attributes[];
  availability: ProductCreate_productCreate_product_availability | null;
  images: (ProductCreate_productCreate_product_images | null)[] | null;
  variants: (ProductCreate_productCreate_product_variants | null)[] | null;
  productType: ProductCreate_productCreate_product_productType;
  url: string;
}

export interface ProductCreate_productCreate {
  __typename: "ProductCreate";
  errors: ProductCreate_productCreate_errors[] | null;
  product: ProductCreate_productCreate_product | null;
}

export interface ProductCreate {
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
  price?: any | null;
  productType: string;
  sku?: string | null;
  stockQuantity?: number | null;
}
