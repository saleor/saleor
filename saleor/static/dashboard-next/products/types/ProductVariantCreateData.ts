/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: ProductVariantCreateData
// ====================================================

export interface ProductVariantCreateData_product_images_edges_node {
  __typename: "ProductImage";
  id: string;
  sortOrder: number;
  url: string;
}

export interface ProductVariantCreateData_product_images_edges {
  __typename: "ProductImageCountableEdge";
  node: ProductVariantCreateData_product_images_edges_node;
}

export interface ProductVariantCreateData_product_images {
  __typename: "ProductImageCountableConnection";
  edges: ProductVariantCreateData_product_images_edges[];
}

export interface ProductVariantCreateData_product_productType_variantAttributes_values {
  __typename: "AttributeValue";
  id: string;
  sortOrder: number;
  name: string | null;
  slug: string | null;
}

export interface ProductVariantCreateData_product_productType_variantAttributes {
  __typename: "Attribute";
  id: string;
  slug: string | null;
  name: string | null;
  values: (ProductVariantCreateData_product_productType_variantAttributes_values | null)[] | null;
}

export interface ProductVariantCreateData_product_productType {
  __typename: "ProductType";
  id: string;
  variantAttributes: (ProductVariantCreateData_product_productType_variantAttributes | null)[] | null;
}

export interface ProductVariantCreateData_product_variants_edges_node_image_edges_node {
  __typename: "ProductImage";
  id: string;
  url: string;
}

export interface ProductVariantCreateData_product_variants_edges_node_image_edges {
  __typename: "ProductImageCountableEdge";
  node: ProductVariantCreateData_product_variants_edges_node_image_edges_node;
}

export interface ProductVariantCreateData_product_variants_edges_node_image {
  __typename: "ProductImageCountableConnection";
  edges: ProductVariantCreateData_product_variants_edges_node_image_edges[];
}

export interface ProductVariantCreateData_product_variants_edges_node {
  __typename: "ProductVariant";
  id: string;
  name: string;
  sku: string;
  image: ProductVariantCreateData_product_variants_edges_node_image | null;
}

export interface ProductVariantCreateData_product_variants_edges {
  __typename: "ProductVariantCountableEdge";
  node: ProductVariantCreateData_product_variants_edges_node;
}

export interface ProductVariantCreateData_product_variants {
  __typename: "ProductVariantCountableConnection";
  edges: ProductVariantCreateData_product_variants_edges[];
}

export interface ProductVariantCreateData_product {
  __typename: "Product";
  id: string;
  images: ProductVariantCreateData_product_images | null;
  productType: ProductVariantCreateData_product_productType;
  variants: ProductVariantCreateData_product_variants | null;
}

export interface ProductVariantCreateData {
  product: ProductVariantCreateData_product | null;
}

export interface ProductVariantCreateDataVariables {
  id: string;
}
