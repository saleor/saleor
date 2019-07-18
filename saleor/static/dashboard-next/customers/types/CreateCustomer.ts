/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { UserCreateInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: CreateCustomer
// ====================================================

export interface CreateCustomer_customerCreate_errors {
  __typename: "Error";
  /**
   * Name of a field that caused the error. A value of
   *         `null` indicates that the error isn't associated with a particular
   *         field.
   */
  field: string | null;
  /**
   * The error message.
   */
  message: string | null;
}

export interface CreateCustomer_customerCreate_user {
  __typename: "User";
  /**
   * The ID of the object.
   */
  id: string;
}

export interface CreateCustomer_customerCreate {
  __typename: "CustomerCreate";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: CreateCustomer_customerCreate_errors[] | null;
  user: CreateCustomer_customerCreate_user | null;
}

export interface CreateCustomer {
  /**
   * Creates a new customer.
   */
  customerCreate: CreateCustomer_customerCreate | null;
}

export interface CreateCustomerVariables {
  input: UserCreateInput;
}
