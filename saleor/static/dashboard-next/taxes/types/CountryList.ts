/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: CountryList
// ====================================================

export interface CountryList_shop_countries {
  __typename: "CountryDisplay";
  country: string;
  code: string;
}

export interface CountryList_shop {
  __typename: "Shop";
  chargeTaxesOnShipping: boolean;
  includeTaxesInPrices: boolean;
  displayGrossPrices: boolean;
  countries: (CountryList_shop_countries | null)[];
}

export interface CountryList {
  shop: CountryList_shop | null;
}
