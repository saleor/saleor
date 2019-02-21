import gql from "graphql-tag";

import { TypedMutation } from "../mutations";
import {
  DeleteShippingZone,
  DeleteShippingZoneVariables
} from "./types/DeleteShippingZone";
import {
  UpdateDefaultWeightUnit,
  UpdateDefaultWeightUnitVariables
} from "./types/UpdateDefaultWeightUnit";

const deleteShippingZone = gql`
  mutation DeleteShippingZone($id: ID!) {
    shippingZoneDelete(id: $id) {
      errors {
        field
        message
      }
    }
  }
`;
export const TypedDeleteShippingZone = TypedMutation<
  DeleteShippingZone,
  DeleteShippingZoneVariables
>(deleteShippingZone);

const updateDefaultWeightUnit = gql`
  mutation UpdateDefaultWeightUnit($unit: WeightUnitsEnum) {
    shopSettingsUpdate(input: { defaultWeightUnit: $unit }) {
      errors {
        field
        message
      }
      shop {
        defaultWeightUnit
      }
    }
  }
`;
export const TypedUpdateDefaultWeightUnit = TypedMutation<
  UpdateDefaultWeightUnit,
  UpdateDefaultWeightUnitVariables
>(updateDefaultWeightUnit);
