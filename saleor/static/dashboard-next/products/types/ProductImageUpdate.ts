/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { AttributeInputTypeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: ProductImageUpdate
// ====================================================

export interface ProductImageUpdate_productImageUpdate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface ProductImageUpdate_productImageUpdate_product_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface ProductImageUpdate_productImageUpdate_product_collections {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface ProductImageUpdate_productImageUpdate_product_basePrice {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface ProductImageUpdate_productImageUpdate_product_margin {
  __typename: "Margin";
  start: number | null;
  stop: number | null;
}

export interface ProductImageUpdate_productImageUpdate_product_purchaseCost_start {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface ProductImageUpdate_productImageUpdate_product_purchaseCost_stop {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface ProductImageUpdate_productImageUpdate_product_purchaseCost {
  __typename: "MoneyRange";
  start: ProductImageUpdate_productImageUpdate_product_purchaseCost_start | null;
  stop: ProductImageUpdate_productImageUpdate_product_purchaseCost_stop | null;
}

export interface ProductImageUpdate_productImageUpdate_product_attributes_attribute_values {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface ProductImageUpdate_productImageUpdate_product_attributes_attribute {
  __typename: "Attribute";
  id: string;
  slug: string | null;
  name: string | null;
  inputType: AttributeInputTypeEnum | null;
  valueRequired: boolean;
  values: (ProductImageUpdate_productImageUpdate_product_attributes_attribute_values | null)[] | null;
}

export interface ProductImageUpdate_productImageUpdate_product_attributes_values {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface ProductImageUpdate_productImageUpdate_product_attributes {
  __typename: "SelectedAttribute";
  attribute: ProductImageUpdate_productImageUpdate_product_attributes_attribute;
  values: (ProductImageUpdate_productImageUpdate_product_attributes_values | null)[];
}

export interface ProductImageUpdate_productImageUpdate_product_pricing_priceRange_start_net {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface ProductImageUpdate_productImageUpdate_product_pricing_priceRange_start {
  __typename: "TaxedMoney";
  net: ProductImageUpdate_productImageUpdate_product_pricing_priceRange_start_net;
}

export interface ProductImageUpdate_productImageUpdate_product_pricing_priceRange_stop_net {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface ProductImageUpdate_productImageUpdate_product_pricing_priceRange_stop {
  __typename: "TaxedMoney";
  net: ProductImageUpdate_productImageUpdate_product_pricing_priceRange_stop_net;
}

export interface ProductImageUpdate_productImageUpdate_product_pricing_priceRange {
  __typename: "TaxedMoneyRange";
  start: ProductImageUpdate_productImageUpdate_product_pricing_priceRange_start | null;
  stop: ProductImageUpdate_productImageUpdate_product_pricing_priceRange_stop | null;
}

export interface ProductImageUpdate_productImageUpdate_product_pricing {
  __typename: "ProductPricingInfo";
  priceRange: ProductImageUpdate_productImageUpdate_product_pricing_priceRange | null;
}

export interface ProductImageUpdate_productImageUpdate_product_images {
  __typename: "ProductImage";
  id: string;
  alt: string;
  sortOrder: number | null;
  url: string;
}

export interface ProductImageUpdate_productImageUpdate_product_variants_priceOverride {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface ProductImageUpdate_productImageUpdate_product_variants {
  __typename: "ProductVariant";
  id: string;
  sku: string;
  name: string;
  priceOverride: ProductImageUpdate_productImageUpdate_product_variants_priceOverride | null;
  margin: number | null;
  quantity: number;
  quantityAllocated: number;
  stockQuantity: number;
}

export interface ProductImageUpdate_productImageUpdate_product_productType {
  __typename: "ProductType";
  id: string;
  name: string;
  hasVariants: boolean;
}

export interface ProductImageUpdate_productImageUpdate_product {
  __typename: "Product";
  id: string;
  name: string;
  descriptionJson: any;
  seoTitle: string | null;
  seoDescription: string | null;
  category: ProductImageUpdate_productImageUpdate_product_category;
  collections: (ProductImageUpdate_productImageUpdate_product_collections | null)[] | null;
  basePrice: ProductImageUpdate_productImageUpdate_product_basePrice | null;
  margin: ProductImageUpdate_productImageUpdate_product_margin | null;
  purchaseCost: ProductImageUpdate_productImageUpdate_product_purchaseCost | null;
  isAvailable: boolean | null;
  isPublished: boolean;
  chargeTaxes: boolean;
  publicationDate: any | null;
  attributes: ProductImageUpdate_productImageUpdate_product_attributes[];
  pricing: ProductImageUpdate_productImageUpdate_product_pricing | null;
  images: (ProductImageUpdate_productImageUpdate_product_images | null)[] | null;
  variants: (ProductImageUpdate_productImageUpdate_product_variants | null)[] | null;
  productType: ProductImageUpdate_productImageUpdate_product_productType;
  url: string;
}

export interface ProductImageUpdate_productImageUpdate {
  __typename: "ProductImageUpdate";
  errors: ProductImageUpdate_productImageUpdate_errors[] | null;
  product: ProductImageUpdate_productImageUpdate_product | null;
}

export interface ProductImageUpdate {
  productImageUpdate: ProductImageUpdate_productImageUpdate | null;
}

export interface ProductImageUpdateVariables {
  id: string;
  alt: string;
}
