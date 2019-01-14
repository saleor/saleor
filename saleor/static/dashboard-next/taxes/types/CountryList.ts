/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: CountryList
// ====================================================

export interface CountryList_shop_countries_vat_reducedRates {
  __typename: "ReducedRate";
  rateType: string;
}

export interface CountryList_shop_countries_vat {
  __typename: "VAT";
  standardRate: number | null;
  reducedRates: (CountryList_shop_countries_vat_reducedRates | null)[] | null;
}

export interface CountryList_shop_countries {
  __typename: "CountryDisplay";
  country: string;
  code: string;
  vat: CountryList_shop_countries_vat | null;
}

export interface CountryList_shop {
  __typename: "Shop";
  countries: (CountryList_shop_countries | null)[];
  displayGrossPrices: boolean | null;
  includeTaxesInPrices: boolean | null;
}

export interface CountryList {
  shop: CountryList_shop | null;
}
