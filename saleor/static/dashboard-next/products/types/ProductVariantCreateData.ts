/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: ProductVariantCreateData
// ====================================================

export interface ProductVariantCreateData_product_images {
  __typename: "ProductImage";
  id: string;
  sortOrder: number;
  url: string;
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

export interface ProductVariantCreateData_product_thumbnail {
  __typename: "Image";
  url: string;
}

export interface ProductVariantCreateData_product_variants_images {
  __typename: "ProductImage";
  id: string;
  url: string;
}

export interface ProductVariantCreateData_product_variants {
  __typename: "ProductVariant";
  id: string;
  name: string;
  sku: string;
  images: (ProductVariantCreateData_product_variants_images | null)[] | null;
}

export interface ProductVariantCreateData_product {
  __typename: "Product";
  id: string;
  images: (ProductVariantCreateData_product_images | null)[] | null;
  name: string;
  productType: ProductVariantCreateData_product_productType;
  thumbnail: ProductVariantCreateData_product_thumbnail | null;
  variants: (ProductVariantCreateData_product_variants | null)[] | null;
}

export interface ProductVariantCreateData {
  product: ProductVariantCreateData_product | null;
}

export interface ProductVariantCreateDataVariables {
  id: string;
}
