/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: StaffAvatarDelete
// ====================================================

export interface StaffAvatarDelete_userAvatarDelete_errors {
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

export interface StaffAvatarDelete_userAvatarDelete_user_avatar {
  __typename: "Image";
  /**
   * The URL of the image.
   */
  url: string;
}

export interface StaffAvatarDelete_userAvatarDelete_user {
  __typename: "User";
  /**
   * The ID of the object.
   */
  id: string;
  avatar: StaffAvatarDelete_userAvatarDelete_user_avatar | null;
}

export interface StaffAvatarDelete_userAvatarDelete {
  __typename: "UserAvatarDelete";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: StaffAvatarDelete_userAvatarDelete_errors[] | null;
  /**
   * An updated user instance.
   */
  user: StaffAvatarDelete_userAvatarDelete_user | null;
}

export interface StaffAvatarDelete {
  /**
   * Deletes a user avatar. Only for staff members.
   */
  userAvatarDelete: StaffAvatarDelete_userAvatarDelete | null;
}
