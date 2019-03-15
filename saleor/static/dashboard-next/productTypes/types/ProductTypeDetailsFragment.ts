/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { TaxRateType } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: ProductTypeDetailsFragment
// ====================================================

export interface ProductTypeDetailsFragment_productAttributes_values {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface ProductTypeDetailsFragment_productAttributes {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
  values: (ProductTypeDetailsFragment_productAttributes_values | null)[] | null;
}

export interface ProductTypeDetailsFragment_variantAttributes_values {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface ProductTypeDetailsFragment_variantAttributes {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
  values: (ProductTypeDetailsFragment_variantAttributes_values | null)[] | null;
}

export interface ProductTypeDetailsFragment_weight {
  __typename: "Weight";
  unit: string;
  value: number;
}

export interface ProductTypeDetailsFragment {
  __typename: "ProductType";
  id: string;
  name: string;
  hasVariants: boolean;
  isShippingRequired: boolean;
  taxRate: TaxRateType | null;
  productAttributes: (ProductTypeDetailsFragment_productAttributes | null)[] | null;
  variantAttributes: (ProductTypeDetailsFragment_variantAttributes | null)[] | null;
  weight: ProductTypeDetailsFragment_weight | null;
}
