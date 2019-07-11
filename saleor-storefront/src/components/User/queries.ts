import gql from "graphql-tag";

import { checkoutAddressFragment } from "../../checkout/queries";
import { TypedMutation } from "../../core/mutations";
import { TokenAuth, TokenAuthVariables } from "./types/TokenAuth";

export const userFragment = gql`
  ${checkoutAddressFragment}
  fragment User on User {
    id
    email
    firstName
    lastName
    isStaff
    defaultShippingAddress {
      ...Address
    }
    defaultBillingAddress {
      ...Address
    }
    addresses {
      ...Address
    }
  }
`;

export const tokenAuthMutation = gql`
  ${userFragment}
  mutation TokenAuth($email: String!, $password: String!) {
    tokenCreate(email: $email, password: $password) {
      token
      errors {
        field
        message
      }
      user {
        ...User
      }
    }
  }
`;

export const tokenVeryficationMutation = gql`
  ${userFragment}
  mutation VerifyToken($token: String!) {
    tokenVerify(token: $token) {
      payload
      user {
        ...User
      }
    }
  }
`;

export const TypedTokenAuthMutation = TypedMutation<
  TokenAuth,
  TokenAuthVariables
>(tokenAuthMutation);
