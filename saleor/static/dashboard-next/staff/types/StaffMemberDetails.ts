/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PermissionEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: StaffMemberDetails
// ====================================================

export interface StaffMemberDetails_user_avatar {
  __typename: "Image";
  /**
   * The URL of the image.
   */
  url: string;
}

export interface StaffMemberDetails_user_permissions {
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

export interface StaffMemberDetails_user {
  __typename: "User";
  /**
   * The ID of the object.
   */
  id: string;
  email: string;
  firstName: string;
  isActive: boolean;
  lastName: string;
  avatar: StaffMemberDetails_user_avatar | null;
  /**
   * List of user's permissions.
   */
  permissions: (StaffMemberDetails_user_permissions | null)[] | null;
}

export interface StaffMemberDetails_shop_permissions {
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

export interface StaffMemberDetails_shop {
  __typename: "Shop";
  /**
   * List of available permissions.
   */
  permissions: (StaffMemberDetails_shop_permissions | null)[];
}

export interface StaffMemberDetails {
  /**
   * Lookup an user by ID.
   */
  user: StaffMemberDetails_user | null;
  /**
   * Represents a shop resources.
   */
  shop: StaffMemberDetails_shop | null;
}

export interface StaffMemberDetailsVariables {
  id: string;
}
