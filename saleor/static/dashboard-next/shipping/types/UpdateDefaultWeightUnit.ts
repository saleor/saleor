/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { WeightUnitsEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: UpdateDefaultWeightUnit
// ====================================================

export interface UpdateDefaultWeightUnit_shopSettingsUpdate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface UpdateDefaultWeightUnit_shopSettingsUpdate_shop {
  __typename: "Shop";
  defaultWeightUnit: WeightUnitsEnum | null;
}

export interface UpdateDefaultWeightUnit_shopSettingsUpdate {
  __typename: "ShopSettingsUpdate";
  errors: UpdateDefaultWeightUnit_shopSettingsUpdate_errors[] | null;
  shop: UpdateDefaultWeightUnit_shopSettingsUpdate_shop | null;
}

export interface UpdateDefaultWeightUnit {
  shopSettingsUpdate: UpdateDefaultWeightUnit_shopSettingsUpdate | null;
}

export interface UpdateDefaultWeightUnitVariables {
  unit?: WeightUnitsEnum | null;
}
