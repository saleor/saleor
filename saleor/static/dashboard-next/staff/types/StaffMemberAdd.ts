/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { StaffCreateInput, PermissionEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: StaffMemberAdd
// ====================================================

export interface StaffMemberAdd_staffCreate_errors {
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

export interface StaffMemberAdd_staffCreate_user_avatar {
  __typename: "Image";
  /**
   * The URL of the image.
   */
  url: string;
}

export interface StaffMemberAdd_staffCreate_user_permissions {
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

export interface StaffMemberAdd_staffCreate_user {
  __typename: "User";
  /**
   * The ID of the object.
   */
  id: string;
  email: string;
  firstName: string;
  isActive: boolean;
  lastName: string;
  avatar: StaffMemberAdd_staffCreate_user_avatar | null;
  /**
   * List of user's permissions.
   */
  permissions: (StaffMemberAdd_staffCreate_user_permissions | null)[] | null;
}

export interface StaffMemberAdd_staffCreate {
  __typename: "StaffCreate";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: StaffMemberAdd_staffCreate_errors[] | null;
  user: StaffMemberAdd_staffCreate_user | null;
}

export interface StaffMemberAdd {
  /**
   * Creates a new staff user.
   */
  staffCreate: StaffMemberAdd_staffCreate | null;
}

export interface StaffMemberAddVariables {
  input: StaffCreateInput;
}
