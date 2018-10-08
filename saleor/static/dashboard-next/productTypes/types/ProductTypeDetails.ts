/* tslint:disable */
// This file was automatically generated and should not be edited.

import { TaxRateType } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: ProductTypeDetails
// ====================================================

export interface ProductTypeDetails_productType_productAttributes_values {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface ProductTypeDetails_productType_productAttributes {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
  values: (ProductTypeDetails_productType_productAttributes_values | null)[] | null;
}

export interface ProductTypeDetails_productType_variantAttributes_values {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface ProductTypeDetails_productType_variantAttributes {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
  values: (ProductTypeDetails_productType_variantAttributes_values | null)[] | null;
}

export interface ProductTypeDetails_productType {
  __typename: "ProductType";
  id: string;
  name: string;
  hasVariants: boolean;
  productAttributes: (ProductTypeDetails_productType_productAttributes | null)[] | null;
  variantAttributes: (ProductTypeDetails_productType_variantAttributes | null)[] | null;
  isShippingRequired: boolean;
  taxRate: TaxRateType | null;
}

export interface ProductTypeDetails {
  productType: ProductTypeDetails_productType | null;
}

export interface ProductTypeDetailsVariables {
  id: string;
}
