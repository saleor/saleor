import gql from "graphql-tag";

import { TypedMutation } from "../../../core/mutations";
import { checkoutFragment } from "../../queries";
import {
  updateCheckoutBillingAddress,
  updateCheckoutBillingAddressVariables
} from "./types/updateCheckoutBillingAddress";

const updateCheckoutBillingAddressMutation = gql`
  ${checkoutFragment}
  mutation updateCheckoutBillingAddress(
    $checkoutId: ID!
    $billingAddress: AddressInput!
  ) {
    checkoutBillingAddressUpdate(
      checkoutId: $checkoutId
      billingAddress: $billingAddress
    ) {
      errors {
        field
        message
      }
      checkout {
        ...Checkout
      }
    }
  }
`;

export const TypedUpdateCheckoutBillingAddressMutation = TypedMutation<
  updateCheckoutBillingAddress,
  updateCheckoutBillingAddressVariables
>(updateCheckoutBillingAddressMutation);
