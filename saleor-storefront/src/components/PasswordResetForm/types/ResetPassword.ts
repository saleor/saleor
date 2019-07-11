/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: ResetPassword
// ====================================================

export interface ResetPassword_customerPasswordReset_errors {
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

export interface ResetPassword_customerPasswordReset {
  __typename: "CustomerPasswordReset";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: ResetPassword_customerPasswordReset_errors[] | null;
}

export interface ResetPassword {
  customerPasswordReset: ResetPassword_customerPasswordReset | null;
}

export interface ResetPasswordVariables {
  email: string;
}
