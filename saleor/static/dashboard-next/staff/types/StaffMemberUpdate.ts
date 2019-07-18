/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { StaffInput, PermissionEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: StaffMemberUpdate
// ====================================================

export interface StaffMemberUpdate_staffUpdate_errors {
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

export interface StaffMemberUpdate_staffUpdate_user_avatar {
  __typename: "Image";
  /**
   * The URL of the image.
   */
  url: string;
}

export interface StaffMemberUpdate_staffUpdate_user_permissions {
  __typename: "PermissionDisplay";
  /**
   * Internal code for permission.
   */
  code: PermissionEnum;
  /**
   * Describe action(s) allowed to do by permission.
   */
  name: string;
}

export interface StaffMemberUpdate_staffUpdate_user {
  __typename: "User";
  /**
   * The ID of the object.
   */
  id: string;
  email: string;
  firstName: string;
  isActive: boolean;
  lastName: string;
  avatar: StaffMemberUpdate_staffUpdate_user_avatar | null;
  /**
   * List of user's permissions.
   */
  permissions: (StaffMemberUpdate_staffUpdate_user_permissions | null)[] | null;
}

export interface StaffMemberUpdate_staffUpdate {
  __typename: "StaffUpdate";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: StaffMemberUpdate_staffUpdate_errors[] | null;
  user: StaffMemberUpdate_staffUpdate_user | null;
}

export interface StaffMemberUpdate {
  /**
   * Updates an existing staff user.
   */
  staffUpdate: StaffMemberUpdate_staffUpdate | null;
}

export interface StaffMemberUpdateVariables {
  id: string;
  input: StaffInput;
}
