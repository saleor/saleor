/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ProductTypeInput, TaxRateType } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: ProductTypeCreate
// ====================================================

export interface ProductTypeCreate_productTypeCreate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface ProductTypeCreate_productTypeCreate_productType_productAttributes_values {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface ProductTypeCreate_productTypeCreate_productType_productAttributes {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
  values: (ProductTypeCreate_productTypeCreate_productType_productAttributes_values | null)[] | null;
}

export interface ProductTypeCreate_productTypeCreate_productType_variantAttributes_values {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface ProductTypeCreate_productTypeCreate_productType_variantAttributes {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
  values: (ProductTypeCreate_productTypeCreate_productType_variantAttributes_values | null)[] | null;
}

export interface ProductTypeCreate_productTypeCreate_productType_weight {
  __typename: "Weight";
  unit: string;
  value: number;
}

export interface ProductTypeCreate_productTypeCreate_productType {
  __typename: "ProductType";
  id: string;
  name: string;
  hasVariants: boolean;
  isShippingRequired: boolean;
  taxRate: TaxRateType | null;
  productAttributes: (ProductTypeCreate_productTypeCreate_productType_productAttributes | null)[] | null;
  variantAttributes: (ProductTypeCreate_productTypeCreate_productType_variantAttributes | null)[] | null;
  weight: ProductTypeCreate_productTypeCreate_productType_weight | null;
}

export interface ProductTypeCreate_productTypeCreate {
  __typename: "ProductTypeCreate";
  errors: ProductTypeCreate_productTypeCreate_errors[] | null;
  productType: ProductTypeCreate_productTypeCreate_productType | null;
}

export interface ProductTypeCreate {
  productTypeCreate: ProductTypeCreate_productTypeCreate | null;
}

export interface ProductTypeCreateVariables {
  input: ProductTypeInput;
}
