/* tslint:disable */
// This file was automatically generated and should not be edited.

import { AuthorizationKeyInput, AuthorizationKeyType } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: AuthorizationKeyAdd
// ====================================================

export interface AuthorizationKeyAdd_authorizationKeyAdd_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface AuthorizationKeyAdd_authorizationKeyAdd {
  __typename: "AuthorizationKeyAdd";
  errors: (AuthorizationKeyAdd_authorizationKeyAdd_errors | null)[] | null;
}

export interface AuthorizationKeyAdd {
  authorizationKeyAdd: AuthorizationKeyAdd_authorizationKeyAdd | null;
}

export interface AuthorizationKeyAddVariables {
  input: AuthorizationKeyInput;
  keyType: AuthorizationKeyType;
}
