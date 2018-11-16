/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: ProductVariantDetails
// ====================================================

export interface ProductVariantDetails_productVariant_attributes_attribute_values {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface ProductVariantDetails_productVariant_attributes_attribute {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
  values: (ProductVariantDetails_productVariant_attributes_attribute_values | null)[] | null;
}

export interface ProductVariantDetails_productVariant_attributes_value {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface ProductVariantDetails_productVariant_attributes {
  __typename: "SelectedAttribute";
  attribute: ProductVariantDetails_productVariant_attributes_attribute;
  value: ProductVariantDetails_productVariant_attributes_value;
}

export interface ProductVariantDetails_productVariant_costPrice {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface ProductVariantDetails_productVariant_images_edges_node {
  __typename: "ProductImage";
  id: string;
}

export interface ProductVariantDetails_productVariant_images_edges {
  __typename: "ProductImageCountableEdge";
  node: ProductVariantDetails_productVariant_images_edges_node;
}

export interface ProductVariantDetails_productVariant_images {
  __typename: "ProductImageCountableConnection";
  edges: ProductVariantDetails_productVariant_images_edges[];
}

export interface ProductVariantDetails_productVariant_priceOverride {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface ProductVariantDetails_productVariant_product_images_edges_node {
  __typename: "ProductImage";
  id: string;
  alt: string;
  sortOrder: number;
  url: string;
}

export interface ProductVariantDetails_productVariant_product_images_edges {
  __typename: "ProductImageCountableEdge";
  node: ProductVariantDetails_productVariant_product_images_edges_node;
}

export interface ProductVariantDetails_productVariant_product_images {
  __typename: "ProductImageCountableConnection";
  edges: ProductVariantDetails_productVariant_product_images_edges[];
}

export interface ProductVariantDetails_productVariant_product_variants_edges_node_image_edges_node {
  __typename: "ProductImage";
  id: string;
  url: string;
}

export interface ProductVariantDetails_productVariant_product_variants_edges_node_image_edges {
  __typename: "ProductImageCountableEdge";
  node: ProductVariantDetails_productVariant_product_variants_edges_node_image_edges_node;
}

export interface ProductVariantDetails_productVariant_product_variants_edges_node_image {
  __typename: "ProductImageCountableConnection";
  edges: ProductVariantDetails_productVariant_product_variants_edges_node_image_edges[];
}

export interface ProductVariantDetails_productVariant_product_variants_edges_node {
  __typename: "ProductVariant";
  id: string;
  name: string;
  sku: string;
  image: ProductVariantDetails_productVariant_product_variants_edges_node_image | null;
}

export interface ProductVariantDetails_productVariant_product_variants_edges {
  __typename: "ProductVariantCountableEdge";
  node: ProductVariantDetails_productVariant_product_variants_edges_node;
}

export interface ProductVariantDetails_productVariant_product_variants {
  __typename: "ProductVariantCountableConnection";
  totalCount: number | null;
  edges: ProductVariantDetails_productVariant_product_variants_edges[];
}

export interface ProductVariantDetails_productVariant_product {
  __typename: "Product";
  id: string;
  images: ProductVariantDetails_productVariant_product_images | null;
  name: string;
  thumbnailUrl: string | null;
  variants: ProductVariantDetails_productVariant_product_variants | null;
}

export interface ProductVariantDetails_productVariant {
  __typename: "ProductVariant";
  id: string;
  attributes: ProductVariantDetails_productVariant_attributes[];
  costPrice: ProductVariantDetails_productVariant_costPrice | null;
  images: ProductVariantDetails_productVariant_images | null;
  name: string;
  priceOverride: ProductVariantDetails_productVariant_priceOverride | null;
  product: ProductVariantDetails_productVariant_product;
  sku: string;
  quantity: number;
  quantityAllocated: number;
}

export interface ProductVariantDetails {
  productVariant: ProductVariantDetails_productVariant | null;
}

export interface ProductVariantDetailsVariables {
  id: string;
}
