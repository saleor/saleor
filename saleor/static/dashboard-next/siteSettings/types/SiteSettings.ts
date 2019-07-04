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

export interface SiteSettings_shop_domain {
  __typename: "Domain";
  host: string;
}

export interface SiteSettings_shop {
  __typename: "Shop";
  authorizationKeys: (SiteSettings_shop_authorizationKeys | null)[];
  description: string | null;
  domain: SiteSettings_shop_domain;
  name: string;
}

export interface SiteSettings {
  shop: SiteSettings_shop | null;
}
