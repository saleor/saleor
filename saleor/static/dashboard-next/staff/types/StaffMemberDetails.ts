/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: StaffMemberDetails
// ====================================================

export interface StaffMemberDetails_user_permissions {
  __typename: "PermissionDisplay";
  code: string;
  name: string;
}

export interface StaffMemberDetails_user {
  __typename: "User";
  id: string;
  email: string;
  isActive: boolean;
  permissions: (StaffMemberDetails_user_permissions | null)[] | null;
}

export interface StaffMemberDetails {
  user: StaffMemberDetails_user | null;
}

export interface StaffMemberDetailsVariables {
  id: string;
}
