/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { TaxRateType } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: UnassignAttribute
// ====================================================

export interface UnassignAttribute_attributeUnassign_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface UnassignAttribute_attributeUnassign_productType_productAttributes {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface UnassignAttribute_attributeUnassign_productType_variantAttributes {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface UnassignAttribute_attributeUnassign_productType_weight {
  __typename: "Weight";
  unit: string;
  value: number;
}

export interface UnassignAttribute_attributeUnassign_productType {
  __typename: "ProductType";
  id: string;
  name: string;
  hasVariants: boolean;
  isShippingRequired: boolean;
  taxRate: TaxRateType | null;
  productAttributes: (UnassignAttribute_attributeUnassign_productType_productAttributes | null)[] | null;
  variantAttributes: (UnassignAttribute_attributeUnassign_productType_variantAttributes | null)[] | null;
  weight: UnassignAttribute_attributeUnassign_productType_weight | null;
}

export interface UnassignAttribute_attributeUnassign {
  __typename: "AttributeUnassign";
  errors: UnassignAttribute_attributeUnassign_errors[] | null;
  productType: UnassignAttribute_attributeUnassign_productType | null;
}

export interface UnassignAttribute {
  attributeUnassign: UnassignAttribute_attributeUnassign | null;
}

export interface UnassignAttributeVariables {
  id: string;
  ids: (string | null)[];
}
