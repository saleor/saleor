import gql from "graphql-tag";
import * as React from "react";
import { Mutation, MutationProps } from "react-apollo";

import { TokenAuthMutation, TokenAuthMutationVariables } from "../gql-types";

export const tokenAuthMutation = gql`
  mutation TokenAuth($email: String!, $password: String!) {
    tokenCreate(email: $email, password: $password) {
      token
    }
  }
`;

export const TypedTokenAuthMutation: React.ComponentType<
  MutationProps<TokenAuthMutation, TokenAuthMutationVariables>
> = Mutation;
