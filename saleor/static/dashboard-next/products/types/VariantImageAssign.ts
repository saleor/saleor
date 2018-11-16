/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: VariantImageAssign
// ====================================================

export interface VariantImageAssign_variantImageAssign_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface VariantImageAssign_variantImageAssign_productVariant_attributes_attribute_values {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface VariantImageAssign_variantImageAssign_productVariant_attributes_attribute {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
  values: (VariantImageAssign_variantImageAssign_productVariant_attributes_attribute_values | null)[] | null;
}

export interface VariantImageAssign_variantImageAssign_productVariant_attributes_value {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface VariantImageAssign_variantImageAssign_productVariant_attributes {
  __typename: "SelectedAttribute";
  attribute: VariantImageAssign_variantImageAssign_productVariant_attributes_attribute;
  value: VariantImageAssign_variantImageAssign_productVariant_attributes_value;
}

export interface VariantImageAssign_variantImageAssign_productVariant_costPrice {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface VariantImageAssign_variantImageAssign_productVariant_images_edges_node {
  __typename: "ProductImage";
  id: string;
}

export interface VariantImageAssign_variantImageAssign_productVariant_images_edges {
  __typename: "ProductImageCountableEdge";
  node: VariantImageAssign_variantImageAssign_productVariant_images_edges_node;
}

export interface VariantImageAssign_variantImageAssign_productVariant_images {
  __typename: "ProductImageCountableConnection";
  edges: VariantImageAssign_variantImageAssign_productVariant_images_edges[];
}

export interface VariantImageAssign_variantImageAssign_productVariant_priceOverride {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface VariantImageAssign_variantImageAssign_productVariant_product_images_edges_node {
  __typename: "ProductImage";
  id: string;
  alt: string;
  sortOrder: number;
  url: string;
}

export interface VariantImageAssign_variantImageAssign_productVariant_product_images_edges {
  __typename: "ProductImageCountableEdge";
  node: VariantImageAssign_variantImageAssign_productVariant_product_images_edges_node;
}

export interface VariantImageAssign_variantImageAssign_productVariant_product_images {
  __typename: "ProductImageCountableConnection";
  edges: VariantImageAssign_variantImageAssign_productVariant_product_images_edges[];
}

export interface VariantImageAssign_variantImageAssign_productVariant_product_variants_edges_node_image_edges_node {
  __typename: "ProductImage";
  id: string;
  url: string;
}

export interface VariantImageAssign_variantImageAssign_productVariant_product_variants_edges_node_image_edges {
  __typename: "ProductImageCountableEdge";
  node: VariantImageAssign_variantImageAssign_productVariant_product_variants_edges_node_image_edges_node;
}

export interface VariantImageAssign_variantImageAssign_productVariant_product_variants_edges_node_image {
  __typename: "ProductImageCountableConnection";
  edges: VariantImageAssign_variantImageAssign_productVariant_product_variants_edges_node_image_edges[];
}

export interface VariantImageAssign_variantImageAssign_productVariant_product_variants_edges_node {
  __typename: "ProductVariant";
  id: string;
  name: string;
  sku: string;
  image: VariantImageAssign_variantImageAssign_productVariant_product_variants_edges_node_image | null;
}

export interface VariantImageAssign_variantImageAssign_productVariant_product_variants_edges {
  __typename: "ProductVariantCountableEdge";
  node: VariantImageAssign_variantImageAssign_productVariant_product_variants_edges_node;
}

export interface VariantImageAssign_variantImageAssign_productVariant_product_variants {
  __typename: "ProductVariantCountableConnection";
  totalCount: number | null;
  edges: VariantImageAssign_variantImageAssign_productVariant_product_variants_edges[];
}

export interface VariantImageAssign_variantImageAssign_productVariant_product {
  __typename: "Product";
  id: string;
  images: VariantImageAssign_variantImageAssign_productVariant_product_images | null;
  name: string;
  thumbnailUrl: string | null;
  variants: VariantImageAssign_variantImageAssign_productVariant_product_variants | null;
}

export interface VariantImageAssign_variantImageAssign_productVariant {
  __typename: "ProductVariant";
  id: string;
  attributes: VariantImageAssign_variantImageAssign_productVariant_attributes[];
  costPrice: VariantImageAssign_variantImageAssign_productVariant_costPrice | null;
  images: VariantImageAssign_variantImageAssign_productVariant_images | null;
  name: string;
  priceOverride: VariantImageAssign_variantImageAssign_productVariant_priceOverride | null;
  product: VariantImageAssign_variantImageAssign_productVariant_product;
  sku: string;
  quantity: number;
  quantityAllocated: number;
}

export interface VariantImageAssign_variantImageAssign {
  __typename: "VariantImageAssign";
  errors: (VariantImageAssign_variantImageAssign_errors | null)[] | null;
  productVariant: VariantImageAssign_variantImageAssign_productVariant | null;
}

export interface VariantImageAssign {
  variantImageAssign: VariantImageAssign_variantImageAssign | null;
}

export interface VariantImageAssignVariables {
  variantId: string;
  imageId: string;
}
