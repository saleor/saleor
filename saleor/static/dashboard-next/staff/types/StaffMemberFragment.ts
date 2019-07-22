/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: StaffMemberFragment
// ====================================================

export interface StaffMemberFragment_avatar {
  __typename: "Image";
  url: string;
}

export interface StaffMemberFragment {
  __typename: "User";
  id: string;
  email: string;
  firstName: string;
  isActive: boolean;
  lastName: string;
  avatar: StaffMemberFragment_avatar | null;
}
