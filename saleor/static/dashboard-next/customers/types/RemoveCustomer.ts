/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: RemoveCustomer
// ====================================================

export interface RemoveCustomer_customerDelete_errors {
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

export interface RemoveCustomer_customerDelete {
  __typename: "CustomerDelete";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: RemoveCustomer_customerDelete_errors[] | null;
}

export interface RemoveCustomer {
  /**
   * Deletes a customer.
   */
  customerDelete: RemoveCustomer_customerDelete | null;
}

export interface RemoveCustomerVariables {
  id: string;
}
