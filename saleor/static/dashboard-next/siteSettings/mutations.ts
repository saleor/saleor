import gql from "graphql-tag";

import { TypedMutation } from "../mutations";
import { shopFragment } from "./queries";
import {
  AuthorizationKeyAdd,
  AuthorizationKeyAddVariables
} from "./types/AuthorizationKeyAdd";
import {
  ShopSettingsUpdate,
  ShopSettingsUpdateVariables
} from "./types/ShopSettingsUpdate";

const authorizationKeyAdd = gql`
  mutation AuthorizationKeyAdd(
    $input: AuthorizationKeyInput!
    $keyType: AuthorizationKeyType!
  ) {
    authorizationKeyAdd(input: $input, keyType: $keyType) {
      errors {
        field
        message
      }
    }
  }
`;
export const TypedAuthorizationKeyAdd = TypedMutation<
  AuthorizationKeyAdd,
  AuthorizationKeyAddVariables
>(authorizationKeyAdd);

const shopSettingsUpdate = gql`
  ${shopFragment}
  mutation ShopSettingsUpdate(
    $shopDomainInput: SiteDomainInput!
    $shopSettingsInput: ShopSettingsInput!
  ) {
    shopSettingsUpdate(input: $shopSettingsInput) {
      errors {
        field
        message
      }
      shop {
        ...ShopFragment
      }
    }
    shopDomainUpdate(input: $shopDomainInput) {
      errors {
        field
        message
      }
      shop {
        domain {
          host
          url
        }
      }
    }
  }
`;
export const TypedShopSettingsUpdate = TypedMutation<
  ShopSettingsUpdate,
  ShopSettingsUpdateVariables
>(shopSettingsUpdate);
