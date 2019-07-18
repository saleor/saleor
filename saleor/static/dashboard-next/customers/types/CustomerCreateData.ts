/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: CustomerCreateData
// ====================================================

export interface CustomerCreateData_shop_countries {
  __typename: "CountryDisplay";
  /**
   * Country code.
   */
  code: string;
  /**
   * Country name.
   */
  country: string;
}

export interface CustomerCreateData_shop {
  __typename: "Shop";
  /**
   * List of countries available in the shop.
   */
  countries: (CustomerCreateData_shop_countries | null)[];
}

export interface CustomerCreateData {
  /**
   * Represents a shop resources.
   */
  shop: CustomerCreateData_shop | null;
}
