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

export interface StaffAvatarDelete_userAvatarDelete_user_avatar {
  __typename: "Image";
  url: string;
}

export interface StaffAvatarDelete_userAvatarDelete_user {
  __typename: "User";
  id: string;
  avatar: StaffAvatarDelete_userAvatarDelete_user_avatar | null;
}

export interface StaffAvatarDelete_userAvatarDelete {
  __typename: "UserAvatarDelete";
  errors: StaffAvatarDelete_userAvatarDelete_errors[] | null;
  user: StaffAvatarDelete_userAvatarDelete_user | null;
}

export interface StaffAvatarDelete {
  userAvatarDelete: StaffAvatarDelete_userAvatarDelete | null;
}
