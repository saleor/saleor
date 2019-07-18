/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { WeightUnitsEnum, LanguageCodeEnum } from "./../../../types/globalTypes";

// ====================================================
// GraphQL query operation: ShopInfo
// ====================================================

export interface ShopInfo_shop_countries {
  __typename: "CountryDisplay";
  /**
   * Country name.
   */
  country: string;
  /**
   * Country code.
   */
  code: string;
}

export interface ShopInfo_shop_defaultCountry {
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

export interface ShopInfo_shop_domain {
  __typename: "Domain";
  /**
   * The host name of the domain.
   */
  host: string;
  /**
   * Shop's absolute URL.
   */
  url: string;
}

export interface ShopInfo_shop_languages {
  __typename: "LanguageDisplay";
  /**
   * Language code.
   */
  code: LanguageCodeEnum;
  /**
   * Language.
   */
  language: string;
}

export interface ShopInfo_shop {
  __typename: "Shop";
  /**
   * List of countries available in the shop.
   */
  countries: (ShopInfo_shop_countries | null)[];
  /**
   * Default shop's country
   */
  defaultCountry: ShopInfo_shop_defaultCountry | null;
  /**
   * Default shop's currency.
   */
  defaultCurrency: string;
  /**
   * Default weight unit
   */
  defaultWeightUnit: WeightUnitsEnum | null;
  /**
   * Display prices with tax in store
   */
  displayGrossPrices: boolean;
  /**
   * Shop's domain data.
   */
  domain: ShopInfo_shop_domain;
  /**
   * List of the shops's supported languages.
   */
  languages: (ShopInfo_shop_languages | null)[];
  /**
   * Include taxes in prices
   */
  includeTaxesInPrices: boolean;
  /**
   * Shop's name.
   */
  name: string;
  /**
   * Enable inventory tracking
   */
  trackInventoryByDefault: boolean | null;
}

export interface ShopInfo {
  /**
   * Represents a shop resources.
   */
  shop: ShopInfo_shop | null;
}
