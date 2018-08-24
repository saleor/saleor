import gql from "graphql-tag";

import { TypedMutation } from "../mutations";

import {
  TokenAuthMutation,
  TokenAuthMutationVariables,
  VerifyTokenMutation,
  VerifyTokenMutationVariables
} from "../gql-types";

export const fragmentUser = gql`
  fragment User on User {
    id
    email
    isStaff
    note
    permissions {
      code
      name
    }
  }
`;

export const tokenAuthMutation = gql`
  ${fragmentUser}
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

export const TypedTokenAuthMutation = TypedMutation<
  TokenAuthMutation,
  TokenAuthMutationVariables
>(tokenAuthMutation);

export const tokenVerifyMutation = gql`
  ${fragmentUser}
  mutation VerifyToken($token: String!) {
    tokenVerify(token: $token) {
      payload
      user {
        ...User
      }
    }
  }
`;

export const TypedVerifyTokenMutation = TypedMutation<
  VerifyTokenMutation,
  VerifyTokenMutationVariables
>(tokenVerifyMutation);
