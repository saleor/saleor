/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PermissionEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: StaffList
// ====================================================

export interface StaffList_staffUsers_edges_node_avatar {
  __typename: "Image";
  url: string;
}

export interface StaffList_staffUsers_edges_node {
  __typename: "User";
  id: string;
  email: string;
  firstName: string;
  isActive: boolean;
  lastName: string;
  avatar: StaffList_staffUsers_edges_node_avatar | null;
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

export interface StaffList_shop_permissions {
  __typename: "PermissionDisplay";
  code: PermissionEnum;
  name: string;
}

export interface StaffList_shop {
  __typename: "Shop";
  permissions: (StaffList_shop_permissions | null)[];
}

export interface StaffList {
  staffUsers: StaffList_staffUsers | null;
  shop: StaffList_shop | null;
}

export interface StaffListVariables {
  first?: number | null;
  after?: string | null;
  last?: number | null;
  before?: string | null;
}
