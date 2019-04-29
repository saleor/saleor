/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: StaffAvatarDelete
// ====================================================

export interface StaffAvatarDelete_userAvatarDelete_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface StaffAvatarDelete_userAvatarDelete {
  __typename: "UserAvatarDelete";
  errors: StaffAvatarDelete_userAvatarDelete_errors[] | null;
}

export interface StaffAvatarDelete {
  userAvatarDelete: StaffAvatarDelete_userAvatarDelete | null;
}
