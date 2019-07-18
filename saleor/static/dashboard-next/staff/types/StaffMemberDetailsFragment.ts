/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PermissionEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: StaffMemberDetailsFragment
// ====================================================

export interface StaffMemberDetailsFragment_avatar {
  __typename: "Image";
  /**
   * The URL of the image.
   */
  url: string;
}

export interface StaffMemberDetailsFragment_permissions {
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

export interface StaffMemberDetailsFragment {
  __typename: "User";
  /**
   * The ID of the object.
   */
  id: string;
  email: string;
  firstName: string;
  isActive: boolean;
  lastName: string;
  avatar: StaffMemberDetailsFragment_avatar | null;
  /**
   * List of user's permissions.
   */
  permissions: (StaffMemberDetailsFragment_permissions | null)[] | null;
}
