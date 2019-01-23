import gql from "graphql-tag";

import { TypedMutation } from "../mutations";
import { countryFragment, shopTaxesFragment } from "./queries";
import { FetchTaxes } from "./types/FetchTaxes";
import {
  UpdateTaxSettings,
  UpdateTaxSettingsVariables
} from "./types/UpdateTaxSettings";

const updateTaxSettings = gql`
  ${shopTaxesFragment}
  mutation UpdateTaxSettings($input: ShopSettingsInput!) {
    shopSettingsUpdate(input: $input) {
      errors {
        field
        message
      }
      shop {
        ...ShopTaxesFragment
      }
    }
  }
`;
export const TypedUpdateTaxSettings = TypedMutation<
  UpdateTaxSettings,
  UpdateTaxSettingsVariables
>(updateTaxSettings);

const fetchTaxes = gql`
  ${countryFragment}
  mutation FetchTaxes {
    shopFetchTaxRates {
      errors {
        field
        message
      }
      shop {
        countries {
          ...CountryFragment
        }
      }
    }
  }
`;
export const TypedFetchTaxes = TypedMutation<FetchTaxes, {}>(fetchTaxes);
