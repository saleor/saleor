/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: StaffMembersBulkDelete
// ====================================================

export interface StaffMembersBulkDelete_staffBulkDelete_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface StaffMembersBulkDelete_staffBulkDelete {
  __typename: "StaffBulkDelete";
  errors: StaffMembersBulkDelete_staffBulkDelete_errors[] | null;
}

export interface StaffMembersBulkDelete {
  staffBulkDelete: StaffMembersBulkDelete_staffBulkDelete | null;
}

export interface StaffMembersBulkDeleteVariables {
  ids: (string | null)[];
}
