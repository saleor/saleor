/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: MenuItemFragment
// ====================================================

export interface MenuItemFragment_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuItemFragment_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuItemFragment_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuItemFragment {
  __typename: "MenuItem";
  category: MenuItemFragment_category | null;
  collection: MenuItemFragment_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuItemFragment_page | null;
  sortOrder: number | null;
  url: string | null;
}
