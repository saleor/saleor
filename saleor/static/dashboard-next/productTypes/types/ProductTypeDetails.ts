/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { WeightUnitsEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: ProductTypeDetails
// ====================================================

export interface ProductTypeDetails_productType_taxType {
  __typename: "TaxType";
  description: string | null;
  taxCode: string | null;
}

export interface ProductTypeDetails_productType_productAttributes {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
  visibleInStorefront: boolean;
  filterableInDashboard: boolean;
  filterableInStorefront: boolean;
}

export interface ProductTypeDetails_productType_variantAttributes {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
  visibleInStorefront: boolean;
  filterableInDashboard: boolean;
  filterableInStorefront: boolean;
}

export interface ProductTypeDetails_productType_weight {
  __typename: "Weight";
  unit: string;
  value: number;
}

export interface ProductTypeDetails_productType {
  __typename: "ProductType";
  id: string;
  name: string;
  hasVariants: boolean;
  isShippingRequired: boolean;
  taxType: ProductTypeDetails_productType_taxType | null;
  productAttributes: (ProductTypeDetails_productType_productAttributes | null)[] | null;
  variantAttributes: (ProductTypeDetails_productType_variantAttributes | null)[] | null;
  weight: ProductTypeDetails_productType_weight | null;
}

export interface ProductTypeDetails_shop {
  __typename: "Shop";
  defaultWeightUnit: WeightUnitsEnum | null;
}

export interface ProductTypeDetails_taxTypes {
  __typename: "TaxType";
  taxCode: string | null;
  description: string | null;
}

export interface ProductTypeDetails {
  productType: ProductTypeDetails_productType | null;
  shop: ProductTypeDetails_shop | null;
  taxTypes: (ProductTypeDetails_taxTypes | null)[] | null;
}

export interface ProductTypeDetailsVariables {
  id: string;
}
