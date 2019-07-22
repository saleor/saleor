/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: MenuDetailsFragment
// ====================================================

export interface MenuDetailsFragment_items_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuDetailsFragment_items_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuDetailsFragment_items_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuDetailsFragment_items_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuDetailsFragment_items_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuDetailsFragment_items_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuDetailsFragment_items_children_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuDetailsFragment_items_children_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuDetailsFragment_items_children_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuDetailsFragment_items_children_children_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuDetailsFragment_items_children_children_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuDetailsFragment_items_children_children_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuDetailsFragment_items_children_children_children_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuDetailsFragment_items_children_children_children_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuDetailsFragment_items_children_children_children_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuDetailsFragment_items_children_children_children_children_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuDetailsFragment_items_children_children_children_children_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuDetailsFragment_items_children_children_children_children_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuDetailsFragment_items_children_children_children_children_children_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuDetailsFragment_items_children_children_children_children_children_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuDetailsFragment_items_children_children_children_children_children_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuDetailsFragment_items_children_children_children_children_children_children {
  __typename: "MenuItem";
  category: MenuDetailsFragment_items_children_children_children_children_children_children_category | null;
  collection: MenuDetailsFragment_items_children_children_children_children_children_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuDetailsFragment_items_children_children_children_children_children_children_page | null;
  sortOrder: number | null;
  url: string | null;
}

export interface MenuDetailsFragment_items_children_children_children_children_children {
  __typename: "MenuItem";
  category: MenuDetailsFragment_items_children_children_children_children_children_category | null;
  collection: MenuDetailsFragment_items_children_children_children_children_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuDetailsFragment_items_children_children_children_children_children_page | null;
  sortOrder: number | null;
  url: string | null;
  children: (MenuDetailsFragment_items_children_children_children_children_children_children | null)[] | null;
}

export interface MenuDetailsFragment_items_children_children_children_children {
  __typename: "MenuItem";
  category: MenuDetailsFragment_items_children_children_children_children_category | null;
  collection: MenuDetailsFragment_items_children_children_children_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuDetailsFragment_items_children_children_children_children_page | null;
  sortOrder: number | null;
  url: string | null;
  children: (MenuDetailsFragment_items_children_children_children_children_children | null)[] | null;
}

export interface MenuDetailsFragment_items_children_children_children {
  __typename: "MenuItem";
  category: MenuDetailsFragment_items_children_children_children_category | null;
  collection: MenuDetailsFragment_items_children_children_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuDetailsFragment_items_children_children_children_page | null;
  sortOrder: number | null;
  url: string | null;
  children: (MenuDetailsFragment_items_children_children_children_children | null)[] | null;
}

export interface MenuDetailsFragment_items_children_children {
  __typename: "MenuItem";
  category: MenuDetailsFragment_items_children_children_category | null;
  collection: MenuDetailsFragment_items_children_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuDetailsFragment_items_children_children_page | null;
  sortOrder: number | null;
  url: string | null;
  children: (MenuDetailsFragment_items_children_children_children | null)[] | null;
}

export interface MenuDetailsFragment_items_children {
  __typename: "MenuItem";
  category: MenuDetailsFragment_items_children_category | null;
  collection: MenuDetailsFragment_items_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuDetailsFragment_items_children_page | null;
  sortOrder: number | null;
  url: string | null;
  children: (MenuDetailsFragment_items_children_children | null)[] | null;
}

export interface MenuDetailsFragment_items {
  __typename: "MenuItem";
  category: MenuDetailsFragment_items_category | null;
  collection: MenuDetailsFragment_items_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuDetailsFragment_items_page | null;
  sortOrder: number | null;
  url: string | null;
  children: (MenuDetailsFragment_items_children | null)[] | null;
}

export interface MenuDetailsFragment {
  __typename: "Menu";
  id: string;
  items: (MenuDetailsFragment_items | null)[] | null;
  name: string;
}
