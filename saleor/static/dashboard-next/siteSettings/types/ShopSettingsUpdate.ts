/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { SiteDomainInput, ShopSettingsInput, AuthorizationKeyType } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: ShopSettingsUpdate
// ====================================================

export interface ShopSettingsUpdate_shopSettingsUpdate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface ShopSettingsUpdate_shopSettingsUpdate_shop_authorizationKeys {
  __typename: "AuthorizationKey";
  key: string;
  name: AuthorizationKeyType;
}

export interface ShopSettingsUpdate_shopSettingsUpdate_shop_domain {
  __typename: "Domain";
  host: string;
}

export interface ShopSettingsUpdate_shopSettingsUpdate_shop {
  __typename: "Shop";
  authorizationKeys: (ShopSettingsUpdate_shopSettingsUpdate_shop_authorizationKeys | null)[];
  description: string | null;
  domain: ShopSettingsUpdate_shopSettingsUpdate_shop_domain;
  name: string;
}

export interface ShopSettingsUpdate_shopSettingsUpdate {
  __typename: "ShopSettingsUpdate";
  errors: ShopSettingsUpdate_shopSettingsUpdate_errors[] | null;
  shop: ShopSettingsUpdate_shopSettingsUpdate_shop | null;
}

export interface ShopSettingsUpdate_shopDomainUpdate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface ShopSettingsUpdate_shopDomainUpdate_shop_domain {
  __typename: "Domain";
  host: string;
  url: string;
}

export interface ShopSettingsUpdate_shopDomainUpdate_shop {
  __typename: "Shop";
  domain: ShopSettingsUpdate_shopDomainUpdate_shop_domain;
}

export interface ShopSettingsUpdate_shopDomainUpdate {
  __typename: "ShopDomainUpdate";
  errors: ShopSettingsUpdate_shopDomainUpdate_errors[] | null;
  shop: ShopSettingsUpdate_shopDomainUpdate_shop | null;
}

export interface ShopSettingsUpdate {
  shopSettingsUpdate: ShopSettingsUpdate_shopSettingsUpdate | null;
  shopDomainUpdate: ShopSettingsUpdate_shopDomainUpdate | null;
}

export interface ShopSettingsUpdateVariables {
  shopDomainInput: SiteDomainInput;
  shopSettingsInput: ShopSettingsInput;
}
