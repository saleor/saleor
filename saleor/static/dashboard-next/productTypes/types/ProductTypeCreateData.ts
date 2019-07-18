/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { WeightUnitsEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: ProductTypeCreateData
// ====================================================

export interface ProductTypeCreateData_shop {
  __typename: "Shop";
  /**
   * Default weight unit
   */
  defaultWeightUnit: WeightUnitsEnum | null;
}

export interface ProductTypeCreateData_taxTypes {
  __typename: "TaxType";
  /**
   * External tax code used to identify given tax group
   */
  taxCode: string | null;
  /**
   * Description of the tax type
   */
  description: string | null;
}

export interface ProductTypeCreateData {
  /**
   * Represents a shop resources.
   */
  shop: ProductTypeCreateData_shop | null;
  /**
   * List of all tax rates available from tax gateway
   */
  taxTypes: (ProductTypeCreateData_taxTypes | null)[] | null;
}
