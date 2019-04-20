/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { AttributeCreateInput, AttributeTypeEnum, TaxRateType } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: AttributeCreate
// ====================================================

export interface AttributeCreate_attributeCreate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface AttributeCreate_attributeCreate_productType_productAttributes_values {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface AttributeCreate_attributeCreate_productType_productAttributes {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
  values: (AttributeCreate_attributeCreate_productType_productAttributes_values | null)[] | null;
}

export interface AttributeCreate_attributeCreate_productType_variantAttributes_values {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface AttributeCreate_attributeCreate_productType_variantAttributes {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
  values: (AttributeCreate_attributeCreate_productType_variantAttributes_values | null)[] | null;
}

export interface AttributeCreate_attributeCreate_productType_weight {
  __typename: "Weight";
  unit: string;
  value: number;
}

export interface AttributeCreate_attributeCreate_productType {
  __typename: "ProductType";
  id: string;
  name: string;
  hasVariants: boolean;
  isShippingRequired: boolean;
  taxRate: TaxRateType | null;
  productAttributes: (AttributeCreate_attributeCreate_productType_productAttributes | null)[] | null;
  variantAttributes: (AttributeCreate_attributeCreate_productType_variantAttributes | null)[] | null;
  weight: AttributeCreate_attributeCreate_productType_weight | null;
}

export interface AttributeCreate_attributeCreate {
  __typename: "AttributeCreate";
  errors: AttributeCreate_attributeCreate_errors[] | null;
  productType: AttributeCreate_attributeCreate_productType | null;
}

export interface AttributeCreate {
  attributeCreate: AttributeCreate_attributeCreate | null;
}

export interface AttributeCreateVariables {
  id: string;
  input: AttributeCreateInput;
  type: AttributeTypeEnum;
}
