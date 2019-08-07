/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ReorderInput, AttributeTypeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: ProductTypeAttributeReorder
// ====================================================

export interface ProductTypeAttributeReorder_productTypeReorderAttributes_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface ProductTypeAttributeReorder_productTypeReorderAttributes_productType_taxType {
  __typename: "TaxType";
  description: string | null;
  taxCode: string | null;
}

export interface ProductTypeAttributeReorder_productTypeReorderAttributes_productType_productAttributes {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
  visibleInStorefront: boolean;
  filterableInDashboard: boolean;
  filterableInStorefront: boolean;
}

export interface ProductTypeAttributeReorder_productTypeReorderAttributes_productType_variantAttributes {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
  visibleInStorefront: boolean;
  filterableInDashboard: boolean;
  filterableInStorefront: boolean;
}

export interface ProductTypeAttributeReorder_productTypeReorderAttributes_productType_weight {
  __typename: "Weight";
  unit: string;
  value: number;
}

export interface ProductTypeAttributeReorder_productTypeReorderAttributes_productType {
  __typename: "ProductType";
  id: string;
  name: string;
  hasVariants: boolean;
  isShippingRequired: boolean;
  taxType: ProductTypeAttributeReorder_productTypeReorderAttributes_productType_taxType | null;
  productAttributes: (ProductTypeAttributeReorder_productTypeReorderAttributes_productType_productAttributes | null)[] | null;
  variantAttributes: (ProductTypeAttributeReorder_productTypeReorderAttributes_productType_variantAttributes | null)[] | null;
  weight: ProductTypeAttributeReorder_productTypeReorderAttributes_productType_weight | null;
}

export interface ProductTypeAttributeReorder_productTypeReorderAttributes {
  __typename: "ProductTypeReorderAttributes";
  errors: ProductTypeAttributeReorder_productTypeReorderAttributes_errors[] | null;
  productType: ProductTypeAttributeReorder_productTypeReorderAttributes_productType | null;
}

export interface ProductTypeAttributeReorder {
  productTypeReorderAttributes: ProductTypeAttributeReorder_productTypeReorderAttributes | null;
}

export interface ProductTypeAttributeReorderVariables {
  move: ReorderInput;
  productTypeId: string;
  type: AttributeTypeEnum;
}
