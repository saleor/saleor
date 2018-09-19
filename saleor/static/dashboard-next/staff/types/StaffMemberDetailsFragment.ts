/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: StaffMemberDetailsFragment
// ====================================================

export interface StaffMemberDetailsFragment_permissions {
  __typename: "PermissionDisplay";
  code: string;
  name: string;
}

export interface StaffMemberDetailsFragment {
  __typename: "User";
  id: string;
  email: string;
  isActive: boolean;
  permissions: (StaffMemberDetailsFragment_permissions | null)[] | null;
}
