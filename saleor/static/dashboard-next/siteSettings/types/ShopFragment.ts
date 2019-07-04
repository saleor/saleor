/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { AuthorizationKeyType } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: ShopFragment
// ====================================================

export interface ShopFragment_authorizationKeys {
  __typename: "AuthorizationKey";
  key: string;
  name: AuthorizationKeyType;
}

export interface ShopFragment_domain {
  __typename: "Domain";
  host: string;
}

export interface ShopFragment {
  __typename: "Shop";
  authorizationKeys: (ShopFragment_authorizationKeys | null)[];
  description: string | null;
  domain: ShopFragment_domain;
  name: string;
}
