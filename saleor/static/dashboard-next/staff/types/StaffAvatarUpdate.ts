/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: StaffAvatarUpdate
// ====================================================

export interface StaffAvatarUpdate_userAvatarUpdate_errors {
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

export interface StaffAvatarUpdate_userAvatarUpdate_user_avatar {
  __typename: "Image";
  /**
   * The URL of the image.
   */
  url: string;
}

export interface StaffAvatarUpdate_userAvatarUpdate_user {
  __typename: "User";
  /**
   * The ID of the object.
   */
  id: string;
  avatar: StaffAvatarUpdate_userAvatarUpdate_user_avatar | null;
}

export interface StaffAvatarUpdate_userAvatarUpdate {
  __typename: "UserAvatarUpdate";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: StaffAvatarUpdate_userAvatarUpdate_errors[] | null;
  /**
   * An updated user instance.
   */
  user: StaffAvatarUpdate_userAvatarUpdate_user | null;
}

export interface StaffAvatarUpdate {
  /**
   * Create a user avatar. Only for staff members. This mutation must
   * be sent as a `multipart` request. More detailed specs of the
   * upload format can be found here:
   * https: // github.com/jaydenseric/graphql-multipart-request-spec
   */
  userAvatarUpdate: StaffAvatarUpdate_userAvatarUpdate | null;
}

export interface StaffAvatarUpdateVariables {
  image: any;
}
