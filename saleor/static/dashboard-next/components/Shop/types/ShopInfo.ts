/* tslint:disable */
// This file was automatically generated and should not be edited.

import { WeightUnitsEnum } from "./../../../types/globalTypes";

// ====================================================
// GraphQL query operation: ShopInfo
// ====================================================

export interface ShopInfo_shop_defaultCountry {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface ShopInfo_shop_domain {
  __typename: "Domain";
  host: string;
  url: string;
}

export interface ShopInfo_shop {
  __typename: "Shop";
  defaultCountry: ShopInfo_shop_defaultCountry | null;
  defaultCurrency: string;
  defaultWeightUnit: WeightUnitsEnum | null;
  displayGrossPrices: boolean | null;
  domain: ShopInfo_shop_domain;
  includeTaxesInPrices: boolean | null;
  name: string;
  trackInventoryByDefault: boolean | null;
}

export interface ShopInfo {
  shop: ShopInfo_shop | null;
}
