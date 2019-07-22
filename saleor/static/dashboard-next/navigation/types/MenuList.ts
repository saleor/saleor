/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: MenuList
// ====================================================

export interface MenuList_menus_edges_node_items {
  __typename: "MenuItem";
  id: string;
}

export interface MenuList_menus_edges_node {
  __typename: "Menu";
  id: string;
  name: string;
  items: (MenuList_menus_edges_node_items | null)[] | null;
}

export interface MenuList_menus_edges {
  __typename: "MenuCountableEdge";
  node: MenuList_menus_edges_node;
}

export interface MenuList_menus_pageInfo {
  __typename: "PageInfo";
  endCursor: string | null;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor: string | null;
}

export interface MenuList_menus {
  __typename: "MenuCountableConnection";
  edges: MenuList_menus_edges[];
  pageInfo: MenuList_menus_pageInfo;
}

export interface MenuList {
  menus: MenuList_menus | null;
}

export interface MenuListVariables {
  first?: number | null;
  after?: string | null;
  last?: number | null;
  before?: string | null;
}
