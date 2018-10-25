import gql from "graphql-tag";

import { TypedMutation } from "../mutations";
import { customerDetailsFragment } from "./queries";
import {
  UpdateCustomer,
  UpdateCustomerVariables
} from "./types/UpdateCustomer";

const updateCustomer = gql`
  ${customerDetailsFragment}
  mutation UpdateCustomer($id: ID!, $input: CustomerInput!) {
    customerUpdate(id: $id, input: $input) {
      errors {
        field
        message
      }
      user {
        ...CustomerDetailsFragment
      }
    }
  }
`;
export const TypedUpdateCustomerMutation = TypedMutation<
  UpdateCustomer,
  UpdateCustomerVariables
>(updateCustomer);
