/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { AttributeInputTypeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: ProductImageCreate
// ====================================================

export interface ProductImageCreate_productImageCreate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface ProductImageCreate_productImageCreate_product_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface ProductImageCreate_productImageCreate_product_collections {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface ProductImageCreate_productImageCreate_product_basePrice {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface ProductImageCreate_productImageCreate_product_margin {
  __typename: "Margin";
  start: number | null;
  stop: number | null;
}

export interface ProductImageCreate_productImageCreate_product_purchaseCost_start {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface ProductImageCreate_productImageCreate_product_purchaseCost_stop {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface ProductImageCreate_productImageCreate_product_purchaseCost {
  __typename: "MoneyRange";
  start: ProductImageCreate_productImageCreate_product_purchaseCost_start | null;
  stop: ProductImageCreate_productImageCreate_product_purchaseCost_stop | null;
}

export interface ProductImageCreate_productImageCreate_product_attributes_attribute_values {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface ProductImageCreate_productImageCreate_product_attributes_attribute {
  __typename: "Attribute";
  id: string;
  slug: string | null;
  name: string | null;
  inputType: AttributeInputTypeEnum | null;
  valueRequired: boolean;
  values: (ProductImageCreate_productImageCreate_product_attributes_attribute_values | null)[] | null;
}

export interface ProductImageCreate_productImageCreate_product_attributes_values {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface ProductImageCreate_productImageCreate_product_attributes {
  __typename: "SelectedAttribute";
  attribute: ProductImageCreate_productImageCreate_product_attributes_attribute;
  values: (ProductImageCreate_productImageCreate_product_attributes_values | null)[];
}

export interface ProductImageCreate_productImageCreate_product_pricing_priceRange_start_net {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface ProductImageCreate_productImageCreate_product_pricing_priceRange_start {
  __typename: "TaxedMoney";
  net: ProductImageCreate_productImageCreate_product_pricing_priceRange_start_net;
}

export interface ProductImageCreate_productImageCreate_product_pricing_priceRange_stop_net {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface ProductImageCreate_productImageCreate_product_pricing_priceRange_stop {
  __typename: "TaxedMoney";
  net: ProductImageCreate_productImageCreate_product_pricing_priceRange_stop_net;
}

export interface ProductImageCreate_productImageCreate_product_pricing_priceRange {
  __typename: "TaxedMoneyRange";
  start: ProductImageCreate_productImageCreate_product_pricing_priceRange_start | null;
  stop: ProductImageCreate_productImageCreate_product_pricing_priceRange_stop | null;
}

export interface ProductImageCreate_productImageCreate_product_pricing {
  __typename: "ProductPricingInfo";
  priceRange: ProductImageCreate_productImageCreate_product_pricing_priceRange | null;
}

export interface ProductImageCreate_productImageCreate_product_images {
  __typename: "ProductImage";
  id: string;
  alt: string;
  sortOrder: number | null;
  url: string;
}

export interface ProductImageCreate_productImageCreate_product_variants_priceOverride {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface ProductImageCreate_productImageCreate_product_variants {
  __typename: "ProductVariant";
  id: string;
  sku: string;
  name: string;
  priceOverride: ProductImageCreate_productImageCreate_product_variants_priceOverride | null;
  margin: number | null;
  quantity: number;
  quantityAllocated: number;
  stockQuantity: number;
}

export interface ProductImageCreate_productImageCreate_product_productType {
  __typename: "ProductType";
  id: string;
  name: string;
  hasVariants: boolean;
}

export interface ProductImageCreate_productImageCreate_product {
  __typename: "Product";
  id: string;
  name: string;
  descriptionJson: any;
  seoTitle: string | null;
  seoDescription: string | null;
  category: ProductImageCreate_productImageCreate_product_category;
  collections: (ProductImageCreate_productImageCreate_product_collections | null)[] | null;
  basePrice: ProductImageCreate_productImageCreate_product_basePrice | null;
  margin: ProductImageCreate_productImageCreate_product_margin | null;
  purchaseCost: ProductImageCreate_productImageCreate_product_purchaseCost | null;
  isAvailable: boolean | null;
  isPublished: boolean;
  chargeTaxes: boolean;
  publicationDate: any | null;
  attributes: ProductImageCreate_productImageCreate_product_attributes[];
  pricing: ProductImageCreate_productImageCreate_product_pricing | null;
  images: (ProductImageCreate_productImageCreate_product_images | null)[] | null;
  variants: (ProductImageCreate_productImageCreate_product_variants | null)[] | null;
  productType: ProductImageCreate_productImageCreate_product_productType;
  url: string;
}

export interface ProductImageCreate_productImageCreate {
  __typename: "ProductImageCreate";
  errors: ProductImageCreate_productImageCreate_errors[] | null;
  product: ProductImageCreate_productImageCreate_product | null;
}

export interface ProductImageCreate {
  productImageCreate: ProductImageCreate_productImageCreate | null;
}

export interface ProductImageCreateVariables {
  product: string;
  image: any;
  alt?: string | null;
}
