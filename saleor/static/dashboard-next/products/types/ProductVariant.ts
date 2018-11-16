/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ProductVariant
// ====================================================

export interface ProductVariant_attributes_attribute_values {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface ProductVariant_attributes_attribute {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
  values: (ProductVariant_attributes_attribute_values | null)[] | null;
}

export interface ProductVariant_attributes_value {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface ProductVariant_attributes {
  __typename: "SelectedAttribute";
  attribute: ProductVariant_attributes_attribute;
  value: ProductVariant_attributes_value;
}

export interface ProductVariant_costPrice {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface ProductVariant_images_edges_node {
  __typename: "ProductImage";
  id: string;
}

export interface ProductVariant_images_edges {
  __typename: "ProductImageCountableEdge";
  node: ProductVariant_images_edges_node;
}

export interface ProductVariant_images {
  __typename: "ProductImageCountableConnection";
  edges: ProductVariant_images_edges[];
}

export interface ProductVariant_priceOverride {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface ProductVariant_product_images_edges_node {
  __typename: "ProductImage";
  id: string;
  alt: string;
  sortOrder: number;
  url: string;
}

export interface ProductVariant_product_images_edges {
  __typename: "ProductImageCountableEdge";
  node: ProductVariant_product_images_edges_node;
}

export interface ProductVariant_product_images {
  __typename: "ProductImageCountableConnection";
  edges: ProductVariant_product_images_edges[];
}

export interface ProductVariant_product_variants_edges_node_image_edges_node {
  __typename: "ProductImage";
  id: string;
  url: string;
}

export interface ProductVariant_product_variants_edges_node_image_edges {
  __typename: "ProductImageCountableEdge";
  node: ProductVariant_product_variants_edges_node_image_edges_node;
}

export interface ProductVariant_product_variants_edges_node_image {
  __typename: "ProductImageCountableConnection";
  edges: ProductVariant_product_variants_edges_node_image_edges[];
}

export interface ProductVariant_product_variants_edges_node {
  __typename: "ProductVariant";
  id: string;
  name: string;
  sku: string;
  image: ProductVariant_product_variants_edges_node_image | null;
}

export interface ProductVariant_product_variants_edges {
  __typename: "ProductVariantCountableEdge";
  node: ProductVariant_product_variants_edges_node;
}

export interface ProductVariant_product_variants {
  __typename: "ProductVariantCountableConnection";
  totalCount: number | null;
  edges: ProductVariant_product_variants_edges[];
}

export interface ProductVariant_product {
  __typename: "Product";
  id: string;
  images: ProductVariant_product_images | null;
  name: string;
  thumbnailUrl: string | null;
  variants: ProductVariant_product_variants | null;
}

export interface ProductVariant {
  __typename: "ProductVariant";
  id: string;
  attributes: ProductVariant_attributes[];
  costPrice: ProductVariant_costPrice | null;
  images: ProductVariant_images | null;
  name: string;
  priceOverride: ProductVariant_priceOverride | null;
  product: ProductVariant_product;
  sku: string;
  quantity: number;
  quantityAllocated: number;
}
