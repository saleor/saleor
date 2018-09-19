/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: StaffList
// ====================================================

export interface StaffList_staffUsers_edges_node {
  __typename: "User";
  id: string;
  email: string;
  isActive: boolean;
}

export interface StaffList_staffUsers_edges {
  __typename: "UserCountableEdge";
  cursor: string;
  node: StaffList_staffUsers_edges_node;
}

export interface StaffList_staffUsers_pageInfo {
  __typename: "PageInfo";
  hasPreviousPage: boolean;
  hasNextPage: boolean;
  startCursor: string | null;
  endCursor: string | null;
}

export interface StaffList_staffUsers {
  __typename: "UserCountableConnection";
  edges: StaffList_staffUsers_edges[];
  pageInfo: StaffList_staffUsers_pageInfo;
}

export interface StaffList {
  staffUsers: StaffList_staffUsers | null;
}

export interface StaffListVariables {
  first?: number | null;
  after?: string | null;
  last?: number | null;
  before?: string | null;
}
