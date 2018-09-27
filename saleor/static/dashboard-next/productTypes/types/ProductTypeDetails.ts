/* tslint:disable */
// This file was automatically generated and should not be edited.

import { TaxRateType } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: ProductTypeDetails
// ====================================================

export interface ProductTypeDetails_productType_productAttributes {
  __typename: "Attribute";
  id: string;
  slug: string | null;
  name: string | null;
}

export interface ProductTypeDetails_productType_variantAttributes {
  __typename: "Attribute";
  id: string;
  slug: string | null;
  name: string | null;
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
