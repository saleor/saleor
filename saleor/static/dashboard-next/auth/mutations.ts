import gql from "graphql-tag";
import * as React from "react";
import { Mutation, MutationProps } from "react-apollo";

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

export const TypedTokenAuthMutation: React.ComponentType<
  MutationProps<TokenAuthMutation, TokenAuthMutationVariables>
> = Mutation;

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

export const TypedVerifyTokenMutation: React.ComponentType<
  MutationProps<VerifyTokenMutation, VerifyTokenMutationVariables>
> = Mutation;
