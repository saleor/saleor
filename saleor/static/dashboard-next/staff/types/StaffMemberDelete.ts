/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: StaffMemberDelete
// ====================================================

export interface StaffMemberDelete_staffDelete_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface StaffMemberDelete_staffDelete {
  __typename: "StaffDelete";
  errors: StaffMemberDelete_staffDelete_errors[] | null;
}

export interface StaffMemberDelete {
  staffDelete: StaffMemberDelete_staffDelete | null;
}

export interface StaffMemberDeleteVariables {
  id: string;
}
