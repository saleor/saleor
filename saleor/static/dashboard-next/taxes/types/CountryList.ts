/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { TaxRateType } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: CountryList
// ====================================================

export interface CountryList_shop_countries_vat_reducedRates {
  __typename: "ReducedRate";
  /**
   * A type of goods.
   */
  rateType: TaxRateType;
  /**
   * Reduced VAT rate in percent.
   */
  rate: number;
}

export interface CountryList_shop_countries_vat {
  __typename: "VAT";
  /**
   * Standard VAT rate in percent.
   */
  standardRate: number | null;
  /**
   * Country's VAT rate exceptions for specific types of goods.
   */
  reducedRates: (CountryList_shop_countries_vat_reducedRates | null)[];
}

export interface CountryList_shop_countries {
  __typename: "CountryDisplay";
  /**
   * Country name.
   */
  country: string;
  /**
   * Country code.
   */
  code: string;
  /**
   * Country tax.
   */
  vat: CountryList_shop_countries_vat | null;
}

export interface CountryList_shop {
  __typename: "Shop";
  /**
   * Charge taxes on shipping
   */
  chargeTaxesOnShipping: boolean;
  /**
   * Include taxes in prices
   */
  includeTaxesInPrices: boolean;
  /**
   * Display prices with tax in store
   */
  displayGrossPrices: boolean;
  /**
   * List of countries available in the shop.
   */
  countries: (CountryList_shop_countries | null)[];
}

export interface CountryList {
  /**
   * Represents a shop resources.
   */
  shop: CountryList_shop | null;
}
