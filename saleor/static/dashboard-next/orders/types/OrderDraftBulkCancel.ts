/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: OrderDraftBulkCancel
// ====================================================

export interface OrderDraftBulkCancel_draftOrderBulkDelete_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface OrderDraftBulkCancel_draftOrderBulkDelete {
  __typename: "DraftOrderBulkDelete";
  errors: OrderDraftBulkCancel_draftOrderBulkDelete_errors[] | null;
}

export interface OrderDraftBulkCancel {
  draftOrderBulkDelete: OrderDraftBulkCancel_draftOrderBulkDelete | null;
}

export interface OrderDraftBulkCancelVariables {
  ids: (string | null)[];
}
