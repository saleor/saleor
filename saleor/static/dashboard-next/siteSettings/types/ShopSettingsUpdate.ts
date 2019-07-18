/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { SiteDomainInput, ShopSettingsInput, AddressInput, AuthorizationKeyType } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: ShopSettingsUpdate
// ====================================================

export interface ShopSettingsUpdate_shopSettingsUpdate_errors {
  __typename: "Error";
  /**
   * Name of a field that caused the error. A value of
   *         `null` indicates that the error isn't associated with a particular
   *         field.
   */
  field: string | null;
  /**
   * The error message.
   */
  message: string | null;
}

export interface ShopSettingsUpdate_shopSettingsUpdate_shop_authorizationKeys {
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

export interface ShopSettingsUpdate_shopSettingsUpdate_shop_companyAddress_country {
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

export interface ShopSettingsUpdate_shopSettingsUpdate_shop_companyAddress {
  __typename: "Address";
  city: string;
  cityArea: string;
  companyName: string;
  /**
   * Default shop's country
   */
  country: ShopSettingsUpdate_shopSettingsUpdate_shop_companyAddress_country;
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

export interface ShopSettingsUpdate_shopSettingsUpdate_shop_countries {
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

export interface ShopSettingsUpdate_shopSettingsUpdate_shop_domain {
  __typename: "Domain";
  /**
   * The host name of the domain.
   */
  host: string;
}

export interface ShopSettingsUpdate_shopSettingsUpdate_shop {
  __typename: "Shop";
  /**
   * List of configured authorization keys. Authorization
   *                keys are used to enable third party OAuth authorization
   *                (currently Facebook or Google).
   */
  authorizationKeys: (ShopSettingsUpdate_shopSettingsUpdate_shop_authorizationKeys | null)[];
  /**
   * Company address
   */
  companyAddress: ShopSettingsUpdate_shopSettingsUpdate_shop_companyAddress | null;
  /**
   * List of countries available in the shop.
   */
  countries: (ShopSettingsUpdate_shopSettingsUpdate_shop_countries | null)[];
  /**
   * Shop's description.
   */
  description: string | null;
  /**
   * Shop's domain data.
   */
  domain: ShopSettingsUpdate_shopSettingsUpdate_shop_domain;
  /**
   * Shop's name.
   */
  name: string;
}

export interface ShopSettingsUpdate_shopSettingsUpdate {
  __typename: "ShopSettingsUpdate";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: ShopSettingsUpdate_shopSettingsUpdate_errors[] | null;
  /**
   * Updated Shop
   */
  shop: ShopSettingsUpdate_shopSettingsUpdate_shop | null;
}

export interface ShopSettingsUpdate_shopDomainUpdate_errors {
  __typename: "Error";
  /**
   * Name of a field that caused the error. A value of
   *         `null` indicates that the error isn't associated with a particular
   *         field.
   */
  field: string | null;
  /**
   * The error message.
   */
  message: string | null;
}

export interface ShopSettingsUpdate_shopDomainUpdate_shop_domain {
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

export interface ShopSettingsUpdate_shopDomainUpdate_shop {
  __typename: "Shop";
  /**
   * Shop's domain data.
   */
  domain: ShopSettingsUpdate_shopDomainUpdate_shop_domain;
}

export interface ShopSettingsUpdate_shopDomainUpdate {
  __typename: "ShopDomainUpdate";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: ShopSettingsUpdate_shopDomainUpdate_errors[] | null;
  /**
   * Updated Shop
   */
  shop: ShopSettingsUpdate_shopDomainUpdate_shop | null;
}

export interface ShopSettingsUpdate_shopAddressUpdate_errors {
  __typename: "Error";
  /**
   * Name of a field that caused the error. A value of
   *         `null` indicates that the error isn't associated with a particular
   *         field.
   */
  field: string | null;
  /**
   * The error message.
   */
  message: string | null;
}

export interface ShopSettingsUpdate_shopAddressUpdate_shop_companyAddress_country {
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

export interface ShopSettingsUpdate_shopAddressUpdate_shop_companyAddress {
  __typename: "Address";
  city: string;
  cityArea: string;
  companyName: string;
  /**
   * Default shop's country
   */
  country: ShopSettingsUpdate_shopAddressUpdate_shop_companyAddress_country;
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

export interface ShopSettingsUpdate_shopAddressUpdate_shop {
  __typename: "Shop";
  /**
   * Company address
   */
  companyAddress: ShopSettingsUpdate_shopAddressUpdate_shop_companyAddress | null;
}

export interface ShopSettingsUpdate_shopAddressUpdate {
  __typename: "ShopAddressUpdate";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: ShopSettingsUpdate_shopAddressUpdate_errors[] | null;
  /**
   * Updated Shop
   */
  shop: ShopSettingsUpdate_shopAddressUpdate_shop | null;
}

export interface ShopSettingsUpdate {
  /**
   * Updates shop settings
   */
  shopSettingsUpdate: ShopSettingsUpdate_shopSettingsUpdate | null;
  /**
   * Updates site domain of the shop
   */
  shopDomainUpdate: ShopSettingsUpdate_shopDomainUpdate | null;
  /**
   * Update shop address
   */
  shopAddressUpdate: ShopSettingsUpdate_shopAddressUpdate | null;
}

export interface ShopSettingsUpdateVariables {
  shopDomainInput: SiteDomainInput;
  shopSettingsInput: ShopSettingsInput;
  addressInput: AddressInput;
}
