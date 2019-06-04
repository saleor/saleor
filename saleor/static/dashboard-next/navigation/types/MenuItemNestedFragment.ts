/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: MenuItemNestedFragment
// ====================================================

export interface MenuItemNestedFragment_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuItemNestedFragment_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuItemNestedFragment_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuItemNestedFragment_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuItemNestedFragment_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuItemNestedFragment_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuItemNestedFragment_children_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuItemNestedFragment_children_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuItemNestedFragment_children_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuItemNestedFragment_children_children_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuItemNestedFragment_children_children_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuItemNestedFragment_children_children_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuItemNestedFragment_children_children_children_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuItemNestedFragment_children_children_children_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuItemNestedFragment_children_children_children_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuItemNestedFragment_children_children_children_children_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuItemNestedFragment_children_children_children_children_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuItemNestedFragment_children_children_children_children_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuItemNestedFragment_children_children_children_children_children_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuItemNestedFragment_children_children_children_children_children_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuItemNestedFragment_children_children_children_children_children_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuItemNestedFragment_children_children_children_children_children_children {
  __typename: "MenuItem";
  category: MenuItemNestedFragment_children_children_children_children_children_children_category | null;
  collection: MenuItemNestedFragment_children_children_children_children_children_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuItemNestedFragment_children_children_children_children_children_children_page | null;
  sortOrder: number | null;
  url: string | null;
}

export interface MenuItemNestedFragment_children_children_children_children_children {
  __typename: "MenuItem";
  category: MenuItemNestedFragment_children_children_children_children_children_category | null;
  collection: MenuItemNestedFragment_children_children_children_children_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuItemNestedFragment_children_children_children_children_children_page | null;
  sortOrder: number | null;
  url: string | null;
  children: (MenuItemNestedFragment_children_children_children_children_children_children | null)[] | null;
}

export interface MenuItemNestedFragment_children_children_children_children {
  __typename: "MenuItem";
  category: MenuItemNestedFragment_children_children_children_children_category | null;
  collection: MenuItemNestedFragment_children_children_children_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuItemNestedFragment_children_children_children_children_page | null;
  sortOrder: number | null;
  url: string | null;
  children: (MenuItemNestedFragment_children_children_children_children_children | null)[] | null;
}

export interface MenuItemNestedFragment_children_children_children {
  __typename: "MenuItem";
  category: MenuItemNestedFragment_children_children_children_category | null;
  collection: MenuItemNestedFragment_children_children_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuItemNestedFragment_children_children_children_page | null;
  sortOrder: number | null;
  url: string | null;
  children: (MenuItemNestedFragment_children_children_children_children | null)[] | null;
}

export interface MenuItemNestedFragment_children_children {
  __typename: "MenuItem";
  category: MenuItemNestedFragment_children_children_category | null;
  collection: MenuItemNestedFragment_children_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuItemNestedFragment_children_children_page | null;
  sortOrder: number | null;
  url: string | null;
  children: (MenuItemNestedFragment_children_children_children | null)[] | null;
}

export interface MenuItemNestedFragment_children {
  __typename: "MenuItem";
  category: MenuItemNestedFragment_children_category | null;
  collection: MenuItemNestedFragment_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuItemNestedFragment_children_page | null;
  sortOrder: number | null;
  url: string | null;
  children: (MenuItemNestedFragment_children_children | null)[] | null;
}

export interface MenuItemNestedFragment {
  __typename: "MenuItem";
  category: MenuItemNestedFragment_category | null;
  collection: MenuItemNestedFragment_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuItemNestedFragment_page | null;
  sortOrder: number | null;
  url: string | null;
  children: (MenuItemNestedFragment_children | null)[] | null;
}
