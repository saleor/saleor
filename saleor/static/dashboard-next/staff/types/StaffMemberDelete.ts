/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: StaffMemberDelete
// ====================================================

export interface StaffMemberDelete_staffDelete_errors {
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

export interface StaffMemberDelete_staffDelete {
  __typename: "StaffDelete";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: StaffMemberDelete_staffDelete_errors[] | null;
}

export interface StaffMemberDelete {
  /**
   * Deletes a staff user.
   */
  staffDelete: StaffMemberDelete_staffDelete | null;
}

export interface StaffMemberDeleteVariables {
  id: string;
}
