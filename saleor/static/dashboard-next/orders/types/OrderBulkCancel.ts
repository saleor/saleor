/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: OrderBulkCancel
// ====================================================

export interface OrderBulkCancel_orderBulkCancel_errors {
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

export interface OrderBulkCancel_orderBulkCancel {
  __typename: "OrderBulkCancel";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: OrderBulkCancel_orderBulkCancel_errors[] | null;
}

export interface OrderBulkCancel {
  /**
   * Cancels orders.
   */
  orderBulkCancel: OrderBulkCancel_orderBulkCancel | null;
}

export interface OrderBulkCancelVariables {
  ids: (string | null)[];
  restock: boolean;
}
