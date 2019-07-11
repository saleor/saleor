import gql from "graphql-tag";

import { TypedMutation } from "../../../core/mutations";
import {
  RegisterCutomer,
  RegisterCutomerVariables
} from "./types/RegisterCutomer";

const customerRegisterMutation = gql`
  mutation RegisterCutomer($email: String!, $password: String!) {
    customerRegister(input: { email: $email, password: $password }) {
      errors {
        field
        message
      }
    }
  }
`;

export const TypedCustomerRegisterMutation = TypedMutation<
  RegisterCutomer,
  RegisterCutomerVariables
>(customerRegisterMutation);
