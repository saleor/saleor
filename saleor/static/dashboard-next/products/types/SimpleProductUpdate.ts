/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { AttributeValueInput, ProductVariantInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: SimpleProductUpdate
// ====================================================

export interface SimpleProductUpdate_productUpdate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface SimpleProductUpdate_productUpdate_product_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface SimpleProductUpdate_productUpdate_product_collections {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface SimpleProductUpdate_productUpdate_product_price {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface SimpleProductUpdate_productUpdate_product_margin {
  __typename: "Margin";
  start: number | null;
  stop: number | null;
}

export interface SimpleProductUpdate_productUpdate_product_purchaseCost_start {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface SimpleProductUpdate_productUpdate_product_purchaseCost_stop {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface SimpleProductUpdate_productUpdate_product_purchaseCost {
  __typename: "MoneyRange";
  start: SimpleProductUpdate_productUpdate_product_purchaseCost_start | null;
  stop: SimpleProductUpdate_productUpdate_product_purchaseCost_stop | null;
}

export interface SimpleProductUpdate_productUpdate_product_attributes_attribute_values {
  __typename: "AttributeValue";
  name: string | null;
  slug: string | null;
}

export interface SimpleProductUpdate_productUpdate_product_attributes_attribute {
  __typename: "Attribute";
  id: string;
  slug: string | null;
  name: string | null;
  values: (SimpleProductUpdate_productUpdate_product_attributes_attribute_values | null)[] | null;
}

export interface SimpleProductUpdate_productUpdate_product_attributes_value {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface SimpleProductUpdate_productUpdate_product_attributes {
  __typename: "SelectedAttribute";
  attribute: SimpleProductUpdate_productUpdate_product_attributes_attribute;
  value: SimpleProductUpdate_productUpdate_product_attributes_value;
}

export interface SimpleProductUpdate_productUpdate_product_availability_priceRange_start_net {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface SimpleProductUpdate_productUpdate_product_availability_priceRange_start {
  __typename: "TaxedMoney";
  net: SimpleProductUpdate_productUpdate_product_availability_priceRange_start_net;
}

export interface SimpleProductUpdate_productUpdate_product_availability_priceRange_stop_net {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface SimpleProductUpdate_productUpdate_product_availability_priceRange_stop {
  __typename: "TaxedMoney";
  net: SimpleProductUpdate_productUpdate_product_availability_priceRange_stop_net;
}

export interface SimpleProductUpdate_productUpdate_product_availability_priceRange {
  __typename: "TaxedMoneyRange";
  start: SimpleProductUpdate_productUpdate_product_availability_priceRange_start | null;
  stop: SimpleProductUpdate_productUpdate_product_availability_priceRange_stop | null;
}

export interface SimpleProductUpdate_productUpdate_product_availability {
  __typename: "ProductAvailability";
  available: boolean | null;
  priceRange: SimpleProductUpdate_productUpdate_product_availability_priceRange | null;
}

export interface SimpleProductUpdate_productUpdate_product_images {
  __typename: "ProductImage";
  id: string;
  alt: string;
  sortOrder: number;
  url: string;
}

export interface SimpleProductUpdate_productUpdate_product_variants_priceOverride {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface SimpleProductUpdate_productUpdate_product_variants {
  __typename: "ProductVariant";
  id: string;
  sku: string;
  name: string;
  priceOverride: SimpleProductUpdate_productUpdate_product_variants_priceOverride | null;
  margin: number | null;
  quantity: number;
  quantityAllocated: number;
  stockQuantity: number;
}

export interface SimpleProductUpdate_productUpdate_product_productType {
  __typename: "ProductType";
  id: string;
  name: string;
  hasVariants: boolean;
}

export interface SimpleProductUpdate_productUpdate_product {
  __typename: "Product";
  id: string;
  name: string;
  descriptionJson: any;
  seoTitle: string | null;
  seoDescription: string | null;
  category: SimpleProductUpdate_productUpdate_product_category;
  collections: (SimpleProductUpdate_productUpdate_product_collections | null)[] | null;
  price: SimpleProductUpdate_productUpdate_product_price | null;
  margin: SimpleProductUpdate_productUpdate_product_margin | null;
  purchaseCost: SimpleProductUpdate_productUpdate_product_purchaseCost | null;
  isPublished: boolean;
  chargeTaxes: boolean;
  publicationDate: any | null;
  attributes: SimpleProductUpdate_productUpdate_product_attributes[];
  availability: SimpleProductUpdate_productUpdate_product_availability | null;
  images: (SimpleProductUpdate_productUpdate_product_images | null)[] | null;
  variants: (SimpleProductUpdate_productUpdate_product_variants | null)[] | null;
  productType: SimpleProductUpdate_productUpdate_product_productType;
  url: string;
}

export interface SimpleProductUpdate_productUpdate {
  __typename: "ProductUpdate";
  errors: SimpleProductUpdate_productUpdate_errors[] | null;
  product: SimpleProductUpdate_productUpdate_product | null;
}

export interface SimpleProductUpdate_productVariantUpdate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface SimpleProductUpdate_productVariantUpdate_productVariant_attributes_attribute_values {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface SimpleProductUpdate_productVariantUpdate_productVariant_attributes_attribute {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
  values: (SimpleProductUpdate_productVariantUpdate_productVariant_attributes_attribute_values | null)[] | null;
}

export interface SimpleProductUpdate_productVariantUpdate_productVariant_attributes_value {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface SimpleProductUpdate_productVariantUpdate_productVariant_attributes {
  __typename: "SelectedAttribute";
  attribute: SimpleProductUpdate_productVariantUpdate_productVariant_attributes_attribute;
  value: SimpleProductUpdate_productVariantUpdate_productVariant_attributes_value;
}

export interface SimpleProductUpdate_productVariantUpdate_productVariant_costPrice {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface SimpleProductUpdate_productVariantUpdate_productVariant_images {
  __typename: "ProductImage";
  id: string;
  url: string;
}

export interface SimpleProductUpdate_productVariantUpdate_productVariant_priceOverride {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface SimpleProductUpdate_productVariantUpdate_productVariant_product_images {
  __typename: "ProductImage";
  id: string;
  alt: string;
  sortOrder: number;
  url: string;
}

export interface SimpleProductUpdate_productVariantUpdate_productVariant_product_thumbnail {
  __typename: "Image";
  url: string;
}

export interface SimpleProductUpdate_productVariantUpdate_productVariant_product_variants_images {
  __typename: "ProductImage";
  id: string;
  url: string;
}

export interface SimpleProductUpdate_productVariantUpdate_productVariant_product_variants {
  __typename: "ProductVariant";
  id: string;
  name: string;
  sku: string;
  images: (SimpleProductUpdate_productVariantUpdate_productVariant_product_variants_images | null)[] | null;
}

export interface SimpleProductUpdate_productVariantUpdate_productVariant_product {
  __typename: "Product";
  id: string;
  images: (SimpleProductUpdate_productVariantUpdate_productVariant_product_images | null)[] | null;
  name: string;
  thumbnail: SimpleProductUpdate_productVariantUpdate_productVariant_product_thumbnail | null;
  variants: (SimpleProductUpdate_productVariantUpdate_productVariant_product_variants | null)[] | null;
}

export interface SimpleProductUpdate_productVariantUpdate_productVariant {
  __typename: "ProductVariant";
  id: string;
  attributes: SimpleProductUpdate_productVariantUpdate_productVariant_attributes[];
  costPrice: SimpleProductUpdate_productVariantUpdate_productVariant_costPrice | null;
  images: (SimpleProductUpdate_productVariantUpdate_productVariant_images | null)[] | null;
  name: string;
  priceOverride: SimpleProductUpdate_productVariantUpdate_productVariant_priceOverride | null;
  product: SimpleProductUpdate_productVariantUpdate_productVariant_product;
  sku: string;
  quantity: number;
  quantityAllocated: number;
}

export interface SimpleProductUpdate_productVariantUpdate {
  __typename: "ProductVariantUpdate";
  errors: SimpleProductUpdate_productVariantUpdate_errors[] | null;
  productVariant: SimpleProductUpdate_productVariantUpdate_productVariant | null;
}

export interface SimpleProductUpdate {
  productUpdate: SimpleProductUpdate_productUpdate | null;
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
  price?: any | null;
  productVariantId: string;
  productVariantInput: ProductVariantInput;
}
