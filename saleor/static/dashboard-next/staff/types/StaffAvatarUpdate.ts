/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: StaffAvatarUpdate
// ====================================================

export interface StaffAvatarUpdate_userAvatarUpdate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface StaffAvatarUpdate_userAvatarUpdate_user_avatar {
  __typename: "Image";
  url: string;
}

export interface StaffAvatarUpdate_userAvatarUpdate_user {
  __typename: "User";
  id: string;
  avatar: StaffAvatarUpdate_userAvatarUpdate_user_avatar | null;
}

export interface StaffAvatarUpdate_userAvatarUpdate {
  __typename: "UserAvatarUpdate";
  errors: StaffAvatarUpdate_userAvatarUpdate_errors[] | null;
  user: StaffAvatarUpdate_userAvatarUpdate_user | null;
}

export interface StaffAvatarUpdate {
  userAvatarUpdate: StaffAvatarUpdate_userAvatarUpdate | null;
}

export interface StaffAvatarUpdateVariables {
  image: any;
}
