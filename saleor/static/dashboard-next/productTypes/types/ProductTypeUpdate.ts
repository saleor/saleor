/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ProductTypeInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: ProductTypeUpdate
// ====================================================

export interface ProductTypeUpdate_productTypeUpdate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface ProductTypeUpdate_productTypeUpdate_productType_taxType {
  __typename: "TaxType";
  description: string | null;
  taxCode: string | null;
}

export interface ProductTypeUpdate_productTypeUpdate_productType_productAttributes {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
  visibleInStorefront: boolean;
  filterableInDashboard: boolean;
  filterableInStorefront: boolean;
}

export interface ProductTypeUpdate_productTypeUpdate_productType_variantAttributes {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
  visibleInStorefront: boolean;
  filterableInDashboard: boolean;
  filterableInStorefront: boolean;
}

export interface ProductTypeUpdate_productTypeUpdate_productType_weight {
  __typename: "Weight";
  unit: string;
  value: number;
}

export interface ProductTypeUpdate_productTypeUpdate_productType {
  __typename: "ProductType";
  id: string;
  name: string;
  hasVariants: boolean;
  isShippingRequired: boolean;
  taxType: ProductTypeUpdate_productTypeUpdate_productType_taxType | null;
  productAttributes: (ProductTypeUpdate_productTypeUpdate_productType_productAttributes | null)[] | null;
  variantAttributes: (ProductTypeUpdate_productTypeUpdate_productType_variantAttributes | null)[] | null;
  weight: ProductTypeUpdate_productTypeUpdate_productType_weight | null;
}

export interface ProductTypeUpdate_productTypeUpdate {
  __typename: "ProductTypeUpdate";
  errors: ProductTypeUpdate_productTypeUpdate_errors[] | null;
  productType: ProductTypeUpdate_productTypeUpdate_productType | null;
}

export interface ProductTypeUpdate {
  productTypeUpdate: ProductTypeUpdate_productTypeUpdate | null;
}

export interface ProductTypeUpdateVariables {
  id: string;
  input: ProductTypeInput;
}
