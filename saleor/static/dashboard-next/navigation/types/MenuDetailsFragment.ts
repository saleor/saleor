/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: MenuDetailsFragment
// ====================================================

export interface MenuDetailsFragment_items_category {
  __typename: "Category";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface MenuDetailsFragment_items_collection {
  __typename: "Collection";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface MenuDetailsFragment_items_page {
  __typename: "Page";
  /**
   * The ID of the object.
   */
  id: string;
  title: string;
}

export interface MenuDetailsFragment_items_children_category {
  __typename: "Category";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface MenuDetailsFragment_items_children_collection {
  __typename: "Collection";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface MenuDetailsFragment_items_children_page {
  __typename: "Page";
  /**
   * The ID of the object.
   */
  id: string;
  title: string;
}

export interface MenuDetailsFragment_items_children_children_category {
  __typename: "Category";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface MenuDetailsFragment_items_children_children_collection {
  __typename: "Collection";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface MenuDetailsFragment_items_children_children_page {
  __typename: "Page";
  /**
   * The ID of the object.
   */
  id: string;
  title: string;
}

export interface MenuDetailsFragment_items_children_children_children_category {
  __typename: "Category";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface MenuDetailsFragment_items_children_children_children_collection {
  __typename: "Collection";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface MenuDetailsFragment_items_children_children_children_page {
  __typename: "Page";
  /**
   * The ID of the object.
   */
  id: string;
  title: string;
}

export interface MenuDetailsFragment_items_children_children_children_children_category {
  __typename: "Category";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface MenuDetailsFragment_items_children_children_children_children_collection {
  __typename: "Collection";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface MenuDetailsFragment_items_children_children_children_children_page {
  __typename: "Page";
  /**
   * The ID of the object.
   */
  id: string;
  title: string;
}

export interface MenuDetailsFragment_items_children_children_children_children_children_category {
  __typename: "Category";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface MenuDetailsFragment_items_children_children_children_children_children_collection {
  __typename: "Collection";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface MenuDetailsFragment_items_children_children_children_children_children_page {
  __typename: "Page";
  /**
   * The ID of the object.
   */
  id: string;
  title: string;
}

export interface MenuDetailsFragment_items_children_children_children_children_children_children_category {
  __typename: "Category";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface MenuDetailsFragment_items_children_children_children_children_children_children_collection {
  __typename: "Collection";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface MenuDetailsFragment_items_children_children_children_children_children_children_page {
  __typename: "Page";
  /**
   * The ID of the object.
   */
  id: string;
  title: string;
}

export interface MenuDetailsFragment_items_children_children_children_children_children_children {
  __typename: "MenuItem";
  category: MenuDetailsFragment_items_children_children_children_children_children_children_category | null;
  collection: MenuDetailsFragment_items_children_children_children_children_children_children_collection | null;
  /**
   * The ID of the object.
   */
  id: string;
  level: number;
  name: string;
  page: MenuDetailsFragment_items_children_children_children_children_children_children_page | null;
  sortOrder: number | null;
  /**
   * URL to the menu item.
   */
  url: string | null;
}

export interface MenuDetailsFragment_items_children_children_children_children_children {
  __typename: "MenuItem";
  category: MenuDetailsFragment_items_children_children_children_children_children_category | null;
  collection: MenuDetailsFragment_items_children_children_children_children_children_collection | null;
  /**
   * The ID of the object.
   */
  id: string;
  level: number;
  name: string;
  page: MenuDetailsFragment_items_children_children_children_children_children_page | null;
  sortOrder: number | null;
  /**
   * URL to the menu item.
   */
  url: string | null;
  children: (MenuDetailsFragment_items_children_children_children_children_children_children | null)[] | null;
}

export interface MenuDetailsFragment_items_children_children_children_children {
  __typename: "MenuItem";
  category: MenuDetailsFragment_items_children_children_children_children_category | null;
  collection: MenuDetailsFragment_items_children_children_children_children_collection | null;
  /**
   * The ID of the object.
   */
  id: string;
  level: number;
  name: string;
  page: MenuDetailsFragment_items_children_children_children_children_page | null;
  sortOrder: number | null;
  /**
   * URL to the menu item.
   */
  url: string | null;
  children: (MenuDetailsFragment_items_children_children_children_children_children | null)[] | null;
}

export interface MenuDetailsFragment_items_children_children_children {
  __typename: "MenuItem";
  category: MenuDetailsFragment_items_children_children_children_category | null;
  collection: MenuDetailsFragment_items_children_children_children_collection | null;
  /**
   * The ID of the object.
   */
  id: string;
  level: number;
  name: string;
  page: MenuDetailsFragment_items_children_children_children_page | null;
  sortOrder: number | null;
  /**
   * URL to the menu item.
   */
  url: string | null;
  children: (MenuDetailsFragment_items_children_children_children_children | null)[] | null;
}

export interface MenuDetailsFragment_items_children_children {
  __typename: "MenuItem";
  category: MenuDetailsFragment_items_children_children_category | null;
  collection: MenuDetailsFragment_items_children_children_collection | null;
  /**
   * The ID of the object.
   */
  id: string;
  level: number;
  name: string;
  page: MenuDetailsFragment_items_children_children_page | null;
  sortOrder: number | null;
  /**
   * URL to the menu item.
   */
  url: string | null;
  children: (MenuDetailsFragment_items_children_children_children | null)[] | null;
}

export interface MenuDetailsFragment_items_children {
  __typename: "MenuItem";
  category: MenuDetailsFragment_items_children_category | null;
  collection: MenuDetailsFragment_items_children_collection | null;
  /**
   * The ID of the object.
   */
  id: string;
  level: number;
  name: string;
  page: MenuDetailsFragment_items_children_page | null;
  sortOrder: number | null;
  /**
   * URL to the menu item.
   */
  url: string | null;
  children: (MenuDetailsFragment_items_children_children | null)[] | null;
}

export interface MenuDetailsFragment_items {
  __typename: "MenuItem";
  category: MenuDetailsFragment_items_category | null;
  collection: MenuDetailsFragment_items_collection | null;
  /**
   * The ID of the object.
   */
  id: string;
  level: number;
  name: string;
  page: MenuDetailsFragment_items_page | null;
  sortOrder: number | null;
  /**
   * URL to the menu item.
   */
  url: string | null;
  children: (MenuDetailsFragment_items_children | null)[] | null;
}

export interface MenuDetailsFragment {
  __typename: "Menu";
  /**
   * The ID of the object.
   */
  id: string;
  items: (MenuDetailsFragment_items | null)[] | null;
  name: string;
}
