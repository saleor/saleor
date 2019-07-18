/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { AuthorizationKeyType } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SiteSettings
// ====================================================

export interface SiteSettings_shop_authorizationKeys {
  __typename: "AuthorizationKey";
  /**
   * Authorization key (client ID).
   */
  key: string;
  /**
   * Name of the authorization backend.
   */
  name: AuthorizationKeyType;
}

export interface SiteSettings_shop_companyAddress_country {
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

export interface SiteSettings_shop_companyAddress {
  __typename: "Address";
  city: string;
  cityArea: string;
  companyName: string;
  /**
   * Default shop's country
   */
  country: SiteSettings_shop_companyAddress_country;
  countryArea: string;
  firstName: string;
  /**
   * The ID of the object.
   */
  id: string;
  lastName: string;
  phone: string | null;
  postalCode: string;
  streetAddress1: string;
  streetAddress2: string;
}

export interface SiteSettings_shop_countries {
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

export interface SiteSettings_shop_domain {
  __typename: "Domain";
  /**
   * The host name of the domain.
   */
  host: string;
}

export interface SiteSettings_shop {
  __typename: "Shop";
  /**
   * List of configured authorization keys. Authorization
   *                keys are used to enable third party OAuth authorization
   *                (currently Facebook or Google).
   */
  authorizationKeys: (SiteSettings_shop_authorizationKeys | null)[];
  /**
   * Company address
   */
  companyAddress: SiteSettings_shop_companyAddress | null;
  /**
   * List of countries available in the shop.
   */
  countries: (SiteSettings_shop_countries | null)[];
  /**
   * Shop's description.
   */
  description: string | null;
  /**
   * Shop's domain data.
   */
  domain: SiteSettings_shop_domain;
  /**
   * Shop's name.
   */
  name: string;
}

export interface SiteSettings {
  /**
   * Represents a shop resources.
   */
  shop: SiteSettings_shop | null;
}
