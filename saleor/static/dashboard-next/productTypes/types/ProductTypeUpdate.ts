/* tslint:disable */
// This file was automatically generated and should not be edited.

import { ProductTypeInput, TaxRateType } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: ProductTypeUpdate
// ====================================================

export interface ProductTypeUpdate_productTypeUpdate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface ProductTypeUpdate_productTypeUpdate_productType_productAttributes_edges_node {
  __typename: "ProductAttribute";
  id: string;
  slug: string | null;
  name: string | null;
}

export interface ProductTypeUpdate_productTypeUpdate_productType_productAttributes_edges {
  __typename: "ProductAttributeCountableEdge";
  node: ProductTypeUpdate_productTypeUpdate_productType_productAttributes_edges_node;
}

export interface ProductTypeUpdate_productTypeUpdate_productType_productAttributes {
  __typename: "ProductAttributeCountableConnection";
  edges: ProductTypeUpdate_productTypeUpdate_productType_productAttributes_edges[];
}

export interface ProductTypeUpdate_productTypeUpdate_productType_variantAttributes_edges_node {
  __typename: "ProductAttribute";
  id: string;
  slug: string | null;
  name: string | null;
}

export interface ProductTypeUpdate_productTypeUpdate_productType_variantAttributes_edges {
  __typename: "ProductAttributeCountableEdge";
  node: ProductTypeUpdate_productTypeUpdate_productType_variantAttributes_edges_node;
}

export interface ProductTypeUpdate_productTypeUpdate_productType_variantAttributes {
  __typename: "ProductAttributeCountableConnection";
  edges: ProductTypeUpdate_productTypeUpdate_productType_variantAttributes_edges[];
}

export interface ProductTypeUpdate_productTypeUpdate_productType {
  __typename: "ProductType";
  id: string;
  name: string;
  hasVariants: boolean;
  taxRate: TaxRateType | null;
  productAttributes: ProductTypeUpdate_productTypeUpdate_productType_productAttributes | null;
  variantAttributes: ProductTypeUpdate_productTypeUpdate_productType_variantAttributes | null;
  isShippingRequired: boolean;
}

export interface ProductTypeUpdate_productTypeUpdate {
  __typename: "ProductTypeUpdate";
  errors: (ProductTypeUpdate_productTypeUpdate_errors | null)[] | null;
  productType: ProductTypeUpdate_productTypeUpdate_productType | null;
}

export interface ProductTypeUpdate {
  productTypeUpdate: ProductTypeUpdate_productTypeUpdate | null;
}

export interface ProductTypeUpdateVariables {
  id: string;
  input: ProductTypeInput;
}
