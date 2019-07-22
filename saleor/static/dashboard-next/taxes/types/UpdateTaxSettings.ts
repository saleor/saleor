/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ShopSettingsInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: UpdateTaxSettings
// ====================================================

export interface UpdateTaxSettings_shopSettingsUpdate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface UpdateTaxSettings_shopSettingsUpdate_shop {
  __typename: "Shop";
  chargeTaxesOnShipping: boolean;
  includeTaxesInPrices: boolean;
  displayGrossPrices: boolean;
}

export interface UpdateTaxSettings_shopSettingsUpdate {
  __typename: "ShopSettingsUpdate";
  errors: UpdateTaxSettings_shopSettingsUpdate_errors[] | null;
  shop: UpdateTaxSettings_shopSettingsUpdate_shop | null;
}

export interface UpdateTaxSettings {
  shopSettingsUpdate: UpdateTaxSettings_shopSettingsUpdate | null;
}

export interface UpdateTaxSettingsVariables {
  input: ShopSettingsInput;
}
