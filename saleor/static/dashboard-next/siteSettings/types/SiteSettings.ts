/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { AuthorizationKeyType } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SiteSettings
// ====================================================

export interface SiteSettings_shop_authorizationKeys {
  __typename: "AuthorizationKey";
  key: string;
  name: AuthorizationKeyType;
}

export interface SiteSettings_shop_companyAddress_country {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface SiteSettings_shop_companyAddress {
  __typename: "Address";
  city: string;
  cityArea: string;
  companyName: string;
  country: SiteSettings_shop_companyAddress_country;
  countryArea: string;
  firstName: string;
  id: string;
  lastName: string;
  phone: string | null;
  postalCode: string;
  streetAddress1: string;
  streetAddress2: string;
}

export interface SiteSettings_shop_countries {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface SiteSettings_shop_domain {
  __typename: "Domain";
  host: string;
}

export interface SiteSettings_shop {
  __typename: "Shop";
  authorizationKeys: (SiteSettings_shop_authorizationKeys | null)[];
  companyAddress: SiteSettings_shop_companyAddress | null;
  countries: (SiteSettings_shop_countries | null)[];
  description: string | null;
  domain: SiteSettings_shop_domain;
  name: string;
}

export interface SiteSettings {
  shop: SiteSettings_shop | null;
}
