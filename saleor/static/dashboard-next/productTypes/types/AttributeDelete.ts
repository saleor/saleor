/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { TaxRateType } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: AttributeDelete
// ====================================================

export interface AttributeDelete_attributeDelete_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface AttributeDelete_attributeDelete_productType_productAttributes_values {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface AttributeDelete_attributeDelete_productType_productAttributes {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
  values: (AttributeDelete_attributeDelete_productType_productAttributes_values | null)[] | null;
}

export interface AttributeDelete_attributeDelete_productType_variantAttributes_values {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface AttributeDelete_attributeDelete_productType_variantAttributes {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
  values: (AttributeDelete_attributeDelete_productType_variantAttributes_values | null)[] | null;
}

export interface AttributeDelete_attributeDelete_productType_weight {
  __typename: "Weight";
  unit: string;
  value: number;
}

export interface AttributeDelete_attributeDelete_productType {
  __typename: "ProductType";
  id: string;
  name: string;
  hasVariants: boolean;
  isShippingRequired: boolean;
  taxRate: TaxRateType | null;
  productAttributes: (AttributeDelete_attributeDelete_productType_productAttributes | null)[] | null;
  variantAttributes: (AttributeDelete_attributeDelete_productType_variantAttributes | null)[] | null;
  weight: AttributeDelete_attributeDelete_productType_weight | null;
}

export interface AttributeDelete_attributeDelete {
  __typename: "AttributeDelete";
  errors: AttributeDelete_attributeDelete_errors[] | null;
  productType: AttributeDelete_attributeDelete_productType | null;
}

export interface AttributeDelete {
  attributeDelete: AttributeDelete_attributeDelete | null;
}

export interface AttributeDeleteVariables {
  id: string;
}
