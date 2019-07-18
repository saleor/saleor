/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PermissionEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: StaffList
// ====================================================

export interface StaffList_staffUsers_edges_node_avatar {
  __typename: "Image";
  /**
   * The URL of the image.
   */
  url: string;
}

export interface StaffList_staffUsers_edges_node {
  __typename: "User";
  /**
   * The ID of the object.
   */
  id: string;
  email: string;
  firstName: string;
  isActive: boolean;
  lastName: string;
  avatar: StaffList_staffUsers_edges_node_avatar | null;
}

export interface StaffList_staffUsers_edges {
  __typename: "UserCountableEdge";
  /**
   * A cursor for use in pagination
   */
  cursor: string;
  /**
   * The item at the end of the edge
   */
  node: StaffList_staffUsers_edges_node;
}

export interface StaffList_staffUsers_pageInfo {
  __typename: "PageInfo";
  /**
   * When paginating backwards, are there more items?
   */
  hasPreviousPage: boolean;
  /**
   * When paginating forwards, are there more items?
   */
  hasNextPage: boolean;
  /**
   * When paginating backwards, the cursor to continue.
   */
  startCursor: string | null;
  /**
   * When paginating forwards, the cursor to continue.
   */
  endCursor: string | null;
}

export interface StaffList_staffUsers {
  __typename: "UserCountableConnection";
  edges: StaffList_staffUsers_edges[];
  /**
   * Pagination data for this connection.
   */
  pageInfo: StaffList_staffUsers_pageInfo;
}

export interface StaffList_shop_permissions {
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

export interface StaffList_shop {
  __typename: "Shop";
  /**
   * List of available permissions.
   */
  permissions: (StaffList_shop_permissions | null)[];
}

export interface StaffList {
  /**
   * List of the shop's staff users.
   */
  staffUsers: StaffList_staffUsers | null;
  /**
   * Represents a shop resources.
   */
  shop: StaffList_shop | null;
}

export interface StaffListVariables {
  first?: number | null;
  after?: string | null;
  last?: number | null;
  before?: string | null;
}
