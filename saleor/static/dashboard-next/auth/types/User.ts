/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: User
// ====================================================

export interface User_permissions {
  __typename: "PermissionDisplay";
  code: string;
  name: string;
}

export interface User {
  __typename: "User";
  id: string;
  email: string;
  isStaff: boolean;
  note: string | null;
  permissions: (User_permissions | null)[] | null;
}
