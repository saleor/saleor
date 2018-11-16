/* tslint:disable */
// This file was automatically generated and should not be edited.

import { AttributeValueInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: VariantCreate
// ====================================================

export interface VariantCreate_productVariantCreate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface VariantCreate_productVariantCreate_productVariant_attributes_attribute_values {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface VariantCreate_productVariantCreate_productVariant_attributes_attribute {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
  values: (VariantCreate_productVariantCreate_productVariant_attributes_attribute_values | null)[] | null;
}

export interface VariantCreate_productVariantCreate_productVariant_attributes_value {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface VariantCreate_productVariantCreate_productVariant_attributes {
  __typename: "SelectedAttribute";
  attribute: VariantCreate_productVariantCreate_productVariant_attributes_attribute;
  value: VariantCreate_productVariantCreate_productVariant_attributes_value;
}

export interface VariantCreate_productVariantCreate_productVariant_costPrice {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface VariantCreate_productVariantCreate_productVariant_images_edges_node {
  __typename: "ProductImage";
  id: string;
}

export interface VariantCreate_productVariantCreate_productVariant_images_edges {
  __typename: "ProductImageCountableEdge";
  node: VariantCreate_productVariantCreate_productVariant_images_edges_node;
}

export interface VariantCreate_productVariantCreate_productVariant_images {
  __typename: "ProductImageCountableConnection";
  edges: VariantCreate_productVariantCreate_productVariant_images_edges[];
}

export interface VariantCreate_productVariantCreate_productVariant_priceOverride {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface VariantCreate_productVariantCreate_productVariant_product_images_edges_node {
  __typename: "ProductImage";
  id: string;
  alt: string;
  sortOrder: number;
  url: string;
}

export interface VariantCreate_productVariantCreate_productVariant_product_images_edges {
  __typename: "ProductImageCountableEdge";
  node: VariantCreate_productVariantCreate_productVariant_product_images_edges_node;
}

export interface VariantCreate_productVariantCreate_productVariant_product_images {
  __typename: "ProductImageCountableConnection";
  edges: VariantCreate_productVariantCreate_productVariant_product_images_edges[];
}

export interface VariantCreate_productVariantCreate_productVariant_product_variants_edges_node_image_edges_node {
  __typename: "ProductImage";
  id: string;
  url: string;
}

export interface VariantCreate_productVariantCreate_productVariant_product_variants_edges_node_image_edges {
  __typename: "ProductImageCountableEdge";
  node: VariantCreate_productVariantCreate_productVariant_product_variants_edges_node_image_edges_node;
}

export interface VariantCreate_productVariantCreate_productVariant_product_variants_edges_node_image {
  __typename: "ProductImageCountableConnection";
  edges: VariantCreate_productVariantCreate_productVariant_product_variants_edges_node_image_edges[];
}

export interface VariantCreate_productVariantCreate_productVariant_product_variants_edges_node {
  __typename: "ProductVariant";
  id: string;
  name: string;
  sku: string;
  image: VariantCreate_productVariantCreate_productVariant_product_variants_edges_node_image | null;
}

export interface VariantCreate_productVariantCreate_productVariant_product_variants_edges {
  __typename: "ProductVariantCountableEdge";
  node: VariantCreate_productVariantCreate_productVariant_product_variants_edges_node;
}

export interface VariantCreate_productVariantCreate_productVariant_product_variants {
  __typename: "ProductVariantCountableConnection";
  totalCount: number | null;
  edges: VariantCreate_productVariantCreate_productVariant_product_variants_edges[];
}

export interface VariantCreate_productVariantCreate_productVariant_product {
  __typename: "Product";
  id: string;
  images: VariantCreate_productVariantCreate_productVariant_product_images | null;
  name: string;
  thumbnailUrl: string | null;
  variants: VariantCreate_productVariantCreate_productVariant_product_variants | null;
}

export interface VariantCreate_productVariantCreate_productVariant {
  __typename: "ProductVariant";
  id: string;
  attributes: VariantCreate_productVariantCreate_productVariant_attributes[];
  costPrice: VariantCreate_productVariantCreate_productVariant_costPrice | null;
  images: VariantCreate_productVariantCreate_productVariant_images | null;
  name: string;
  priceOverride: VariantCreate_productVariantCreate_productVariant_priceOverride | null;
  product: VariantCreate_productVariantCreate_productVariant_product;
  sku: string;
  quantity: number;
  quantityAllocated: number;
}

export interface VariantCreate_productVariantCreate {
  __typename: "ProductVariantCreate";
  errors: (VariantCreate_productVariantCreate_errors | null)[] | null;
  productVariant: VariantCreate_productVariantCreate_productVariant | null;
}

export interface VariantCreate {
  productVariantCreate: VariantCreate_productVariantCreate | null;
}

export interface VariantCreateVariables {
  attributes: (AttributeValueInput | null)[];
  costPrice?: any | null;
  priceOverride?: any | null;
  product: string;
  sku?: string | null;
  quantity?: number | null;
  trackInventory: boolean;
}
