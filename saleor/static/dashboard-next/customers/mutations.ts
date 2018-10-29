import gql from "graphql-tag";

import { TypedMutation } from "../mutations";
import { customerDetailsFragment } from "./queries";
import {
  CreateCustomer,
  CreateCustomerVariables
} from "./types/CreateCustomer";
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

const createCustomer = gql`
  mutation CreateCustomer($input: UserCreateInput!) {
    customerCreate(input: $input) {
      errors {
        field
        message
      }
      user {
        id
      }
    }
  }
`;
export const TypedCreateCustomerMutation = TypedMutation<
  CreateCustomer,
  CreateCustomerVariables
>(createCustomer);
