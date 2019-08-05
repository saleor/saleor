/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: UnassignAttribute
// ====================================================

export interface UnassignAttribute_attributeUnassign_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface UnassignAttribute_attributeUnassign_productType_taxType {
  __typename: "TaxType";
  description: string | null;
  taxCode: string | null;
}

export interface UnassignAttribute_attributeUnassign_productType_productAttributes {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
  visibleInStorefront: boolean;
  filterableInDashboard: boolean;
  filterableInStorefront: boolean;
}

export interface UnassignAttribute_attributeUnassign_productType_variantAttributes {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
  visibleInStorefront: boolean;
  filterableInDashboard: boolean;
  filterableInStorefront: boolean;
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
  taxType: UnassignAttribute_attributeUnassign_productType_taxType | null;
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
