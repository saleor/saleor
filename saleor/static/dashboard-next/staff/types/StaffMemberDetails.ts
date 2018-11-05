/* tslint:disable */
// This file was automatically generated and should not be edited.

import { PermissionEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: StaffMemberDetails
// ====================================================

export interface StaffMemberDetails_user_permissions {
  __typename: "PermissionDisplay";
  code: PermissionEnum;
  name: string;
}

export interface StaffMemberDetails_user {
  __typename: "User";
  id: string;
  email: string;
  isActive: boolean;
  permissions: (StaffMemberDetails_user_permissions | null)[] | null;
  firstName: string;
  lastName: string;
}

export interface StaffMemberDetails_shop_permissions {
  __typename: "PermissionDisplay";
  code: PermissionEnum;
  name: string;
}

export interface StaffMemberDetails_shop {
  __typename: "Shop";
  permissions: (StaffMemberDetails_shop_permissions | null)[];
}

export interface StaffMemberDetails {
  user: StaffMemberDetails_user | null;
  shop: StaffMemberDetails_shop | null;
}

export interface StaffMemberDetailsVariables {
  id: string;
}
