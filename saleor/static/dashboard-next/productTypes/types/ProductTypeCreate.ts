/* tslint:disable */
// This file was automatically generated and should not be edited.

import { ProductTypeInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: ProductTypeCreate
// ====================================================

export interface ProductTypeCreate_productTypeCreate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface ProductTypeCreate_productTypeCreate_productType_productAttributes {
  __typename: "Attribute";
  id: string;
  slug: string | null;
  name: string | null;
}

export interface ProductTypeCreate_productTypeCreate_productType_variantAttributes {
  __typename: "Attribute";
  id: string;
  slug: string | null;
  name: string | null;
}

export interface ProductTypeCreate_productTypeCreate_productType {
  __typename: "ProductType";
  id: string;
  name: string;
  hasVariants: boolean;
  productAttributes: (ProductTypeCreate_productTypeCreate_productType_productAttributes | null)[] | null;
  variantAttributes: (ProductTypeCreate_productTypeCreate_productType_variantAttributes | null)[] | null;
  isShippingRequired: boolean;
}

export interface ProductTypeCreate_productTypeCreate {
  __typename: "ProductTypeCreate";
  errors: (ProductTypeCreate_productTypeCreate_errors | null)[] | null;
  productType: ProductTypeCreate_productTypeCreate_productType | null;
}

export interface ProductTypeCreate {
  productTypeCreate: ProductTypeCreate_productTypeCreate | null;
}

export interface ProductTypeCreateVariables {
  input: ProductTypeInput;
}
