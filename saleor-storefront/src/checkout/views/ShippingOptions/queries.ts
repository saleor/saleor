import gql from "graphql-tag";

import { TypedMutation } from "../../../core/mutations";
import { checkoutFragment } from "../../queries";
import {
  updateCheckoutShippingOptions,
  updateCheckoutShippingOptionsVariables
} from "./types/updateCheckoutShippingOptions";

const updateCheckoutShippingOptionsMutation = gql`
  ${checkoutFragment}
  mutation updateCheckoutShippingOptions(
    $checkoutId: ID!
    $shippingMethodId: ID!
  ) {
    checkoutShippingMethodUpdate(
      checkoutId: $checkoutId
      shippingMethodId: $shippingMethodId
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

export const TypedUpdateCheckoutShippingOptionsMutation = TypedMutation<
  updateCheckoutShippingOptions,
  updateCheckoutShippingOptionsVariables
>(updateCheckoutShippingOptionsMutation);
