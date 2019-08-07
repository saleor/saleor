/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { AttributeAssignInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: AssignAttribute
// ====================================================

export interface AssignAttribute_attributeAssign_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface AssignAttribute_attributeAssign_productType_taxType {
  __typename: "TaxType";
  description: string | null;
  taxCode: string | null;
}

export interface AssignAttribute_attributeAssign_productType_productAttributes {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
  visibleInStorefront: boolean;
  filterableInDashboard: boolean;
  filterableInStorefront: boolean;
}

export interface AssignAttribute_attributeAssign_productType_variantAttributes {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
  visibleInStorefront: boolean;
  filterableInDashboard: boolean;
  filterableInStorefront: boolean;
}

export interface AssignAttribute_attributeAssign_productType_weight {
  __typename: "Weight";
  unit: string;
  value: number;
}

export interface AssignAttribute_attributeAssign_productType {
  __typename: "ProductType";
  id: string;
  name: string;
  hasVariants: boolean;
  isShippingRequired: boolean;
  taxType: AssignAttribute_attributeAssign_productType_taxType | null;
  productAttributes: (AssignAttribute_attributeAssign_productType_productAttributes | null)[] | null;
  variantAttributes: (AssignAttribute_attributeAssign_productType_variantAttributes | null)[] | null;
  weight: AssignAttribute_attributeAssign_productType_weight | null;
}

export interface AssignAttribute_attributeAssign {
  __typename: "AttributeAssign";
  errors: AssignAttribute_attributeAssign_errors[] | null;
  productType: AssignAttribute_attributeAssign_productType | null;
}

export interface AssignAttribute {
  attributeAssign: AssignAttribute_attributeAssign | null;
}

export interface AssignAttributeVariables {
  id: string;
  operations: AttributeAssignInput[];
}
