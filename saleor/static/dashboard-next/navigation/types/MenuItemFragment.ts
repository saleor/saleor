/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: MenuItemFragment
// ====================================================

export interface MenuItemFragment_category {
  __typename: "Category";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface MenuItemFragment_collection {
  __typename: "Collection";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface MenuItemFragment_page {
  __typename: "Page";
  /**
   * The ID of the object.
   */
  id: string;
  title: string;
}

export interface MenuItemFragment {
  __typename: "MenuItem";
  category: MenuItemFragment_category | null;
  collection: MenuItemFragment_collection | null;
  /**
   * The ID of the object.
   */
  id: string;
  level: number;
  name: string;
  page: MenuItemFragment_page | null;
  sortOrder: number | null;
  /**
   * URL to the menu item.
   */
  url: string | null;
}
