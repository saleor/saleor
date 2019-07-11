/* tslint:disable */
// This file was automatically generated and should not be edited.

import { PaymentInput } from "./../../../../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: createPayment
// ====================================================

export interface createPayment_checkoutPaymentCreate_errors {
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

export interface createPayment_checkoutPaymentCreate {
  __typename: "CheckoutPaymentCreate";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: createPayment_checkoutPaymentCreate_errors[] | null;
}

export interface createPayment {
  checkoutPaymentCreate: createPayment_checkoutPaymentCreate | null;
}

export interface createPaymentVariables {
  input: PaymentInput;
  checkoutId: string;
}
