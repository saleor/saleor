/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: OrderBulkCancel
// ====================================================

export interface OrderBulkCancel_orderBulkCancel_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface OrderBulkCancel_orderBulkCancel {
  __typename: "OrderBulkCancel";
  errors: OrderBulkCancel_orderBulkCancel_errors[] | null;
}

export interface OrderBulkCancel {
  orderBulkCancel: OrderBulkCancel_orderBulkCancel | null;
}

export interface OrderBulkCancelVariables {
  ids: (string | null)[];
  restock: boolean;
}
