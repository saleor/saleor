/* tslint:disable */
// This file was automatically generated and should not be edited.

import { TaxRateType } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: ProductTypeDetails
// ====================================================

export interface ProductTypeDetails_productType_productAttributes_edges_node {
  __typename: "ProductAttribute";
  id: string;
  slug: string | null;
  name: string | null;
}

export interface ProductTypeDetails_productType_productAttributes_edges {
  __typename: "ProductAttributeCountableEdge";
  node: ProductTypeDetails_productType_productAttributes_edges_node;
}

export interface ProductTypeDetails_productType_productAttributes {
  __typename: "ProductAttributeCountableConnection";
  edges: ProductTypeDetails_productType_productAttributes_edges[];
}

export interface ProductTypeDetails_productType_variantAttributes_edges_node {
  __typename: "ProductAttribute";
  id: string;
  slug: string | null;
  name: string | null;
}

export interface ProductTypeDetails_productType_variantAttributes_edges {
  __typename: "ProductAttributeCountableEdge";
  node: ProductTypeDetails_productType_variantAttributes_edges_node;
}

export interface ProductTypeDetails_productType_variantAttributes {
  __typename: "ProductAttributeCountableConnection";
  edges: ProductTypeDetails_productType_variantAttributes_edges[];
}

export interface ProductTypeDetails_productType {
  __typename: "ProductType";
  id: string;
  name: string;
  hasVariants: boolean;
  productAttributes: ProductTypeDetails_productType_productAttributes | null;
  variantAttributes: ProductTypeDetails_productType_variantAttributes | null;
  isShippingRequired: boolean;
  taxRate: TaxRateType | null;
}

export interface ProductTypeDetails {
  productType: ProductTypeDetails_productType | null;
}

export interface ProductTypeDetailsVariables {
  id: string;
}
