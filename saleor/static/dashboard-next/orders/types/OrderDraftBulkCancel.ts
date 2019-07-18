/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: OrderDraftBulkCancel
// ====================================================

export interface OrderDraftBulkCancel_draftOrderBulkDelete_errors {
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

export interface OrderDraftBulkCancel_draftOrderBulkDelete {
  __typename: "DraftOrderBulkDelete";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: OrderDraftBulkCancel_draftOrderBulkDelete_errors[] | null;
}

export interface OrderDraftBulkCancel {
  /**
   * Deletes draft orders.
   */
  draftOrderBulkDelete: OrderDraftBulkCancel_draftOrderBulkDelete | null;
}

export interface OrderDraftBulkCancelVariables {
  ids: (string | null)[];
}
