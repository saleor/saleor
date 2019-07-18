/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: MenuDetails
// ====================================================

export interface MenuDetails_menu_items_category {
  __typename: "Category";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface MenuDetails_menu_items_collection {
  __typename: "Collection";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface MenuDetails_menu_items_page {
  __typename: "Page";
  /**
   * The ID of the object.
   */
  id: string;
  title: string;
}

export interface MenuDetails_menu_items_children_category {
  __typename: "Category";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface MenuDetails_menu_items_children_collection {
  __typename: "Collection";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface MenuDetails_menu_items_children_page {
  __typename: "Page";
  /**
   * The ID of the object.
   */
  id: string;
  title: string;
}

export interface MenuDetails_menu_items_children_children_category {
  __typename: "Category";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface MenuDetails_menu_items_children_children_collection {
  __typename: "Collection";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface MenuDetails_menu_items_children_children_page {
  __typename: "Page";
  /**
   * The ID of the object.
   */
  id: string;
  title: string;
}

export interface MenuDetails_menu_items_children_children_children_category {
  __typename: "Category";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface MenuDetails_menu_items_children_children_children_collection {
  __typename: "Collection";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface MenuDetails_menu_items_children_children_children_page {
  __typename: "Page";
  /**
   * The ID of the object.
   */
  id: string;
  title: string;
}

export interface MenuDetails_menu_items_children_children_children_children_category {
  __typename: "Category";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface MenuDetails_menu_items_children_children_children_children_collection {
  __typename: "Collection";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface MenuDetails_menu_items_children_children_children_children_page {
  __typename: "Page";
  /**
   * The ID of the object.
   */
  id: string;
  title: string;
}

export interface MenuDetails_menu_items_children_children_children_children_children_category {
  __typename: "Category";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface MenuDetails_menu_items_children_children_children_children_children_collection {
  __typename: "Collection";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface MenuDetails_menu_items_children_children_children_children_children_page {
  __typename: "Page";
  /**
   * The ID of the object.
   */
  id: string;
  title: string;
}

export interface MenuDetails_menu_items_children_children_children_children_children_children_category {
  __typename: "Category";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface MenuDetails_menu_items_children_children_children_children_children_children_collection {
  __typename: "Collection";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface MenuDetails_menu_items_children_children_children_children_children_children_page {
  __typename: "Page";
  /**
   * The ID of the object.
   */
  id: string;
  title: string;
}

export interface MenuDetails_menu_items_children_children_children_children_children_children {
  __typename: "MenuItem";
  category: MenuDetails_menu_items_children_children_children_children_children_children_category | null;
  collection: MenuDetails_menu_items_children_children_children_children_children_children_collection | null;
  /**
   * The ID of the object.
   */
  id: string;
  level: number;
  name: string;
  page: MenuDetails_menu_items_children_children_children_children_children_children_page | null;
  sortOrder: number | null;
  /**
   * URL to the menu item.
   */
  url: string | null;
}

export interface MenuDetails_menu_items_children_children_children_children_children {
  __typename: "MenuItem";
  category: MenuDetails_menu_items_children_children_children_children_children_category | null;
  collection: MenuDetails_menu_items_children_children_children_children_children_collection | null;
  /**
   * The ID of the object.
   */
  id: string;
  level: number;
  name: string;
  page: MenuDetails_menu_items_children_children_children_children_children_page | null;
  sortOrder: number | null;
  /**
   * URL to the menu item.
   */
  url: string | null;
  children: (MenuDetails_menu_items_children_children_children_children_children_children | null)[] | null;
}

export interface MenuDetails_menu_items_children_children_children_children {
  __typename: "MenuItem";
  category: MenuDetails_menu_items_children_children_children_children_category | null;
  collection: MenuDetails_menu_items_children_children_children_children_collection | null;
  /**
   * The ID of the object.
   */
  id: string;
  level: number;
  name: string;
  page: MenuDetails_menu_items_children_children_children_children_page | null;
  sortOrder: number | null;
  /**
   * URL to the menu item.
   */
  url: string | null;
  children: (MenuDetails_menu_items_children_children_children_children_children | null)[] | null;
}

export interface MenuDetails_menu_items_children_children_children {
  __typename: "MenuItem";
  category: MenuDetails_menu_items_children_children_children_category | null;
  collection: MenuDetails_menu_items_children_children_children_collection | null;
  /**
   * The ID of the object.
   */
  id: string;
  level: number;
  name: string;
  page: MenuDetails_menu_items_children_children_children_page | null;
  sortOrder: number | null;
  /**
   * URL to the menu item.
   */
  url: string | null;
  children: (MenuDetails_menu_items_children_children_children_children | null)[] | null;
}

export interface MenuDetails_menu_items_children_children {
  __typename: "MenuItem";
  category: MenuDetails_menu_items_children_children_category | null;
  collection: MenuDetails_menu_items_children_children_collection | null;
  /**
   * The ID of the object.
   */
  id: string;
  level: number;
  name: string;
  page: MenuDetails_menu_items_children_children_page | null;
  sortOrder: number | null;
  /**
   * URL to the menu item.
   */
  url: string | null;
  children: (MenuDetails_menu_items_children_children_children | null)[] | null;
}

export interface MenuDetails_menu_items_children {
  __typename: "MenuItem";
  category: MenuDetails_menu_items_children_category | null;
  collection: MenuDetails_menu_items_children_collection | null;
  /**
   * The ID of the object.
   */
  id: string;
  level: number;
  name: string;
  page: MenuDetails_menu_items_children_page | null;
  sortOrder: number | null;
  /**
   * URL to the menu item.
   */
  url: string | null;
  children: (MenuDetails_menu_items_children_children | null)[] | null;
}

export interface MenuDetails_menu_items {
  __typename: "MenuItem";
  category: MenuDetails_menu_items_category | null;
  collection: MenuDetails_menu_items_collection | null;
  /**
   * The ID of the object.
   */
  id: string;
  level: number;
  name: string;
  page: MenuDetails_menu_items_page | null;
  sortOrder: number | null;
  /**
   * URL to the menu item.
   */
  url: string | null;
  children: (MenuDetails_menu_items_children | null)[] | null;
}

export interface MenuDetails_menu {
  __typename: "Menu";
  /**
   * The ID of the object.
   */
  id: string;
  items: (MenuDetails_menu_items | null)[] | null;
  name: string;
}

export interface MenuDetails {
  /**
   * Lookup a menu by ID or name.
   */
  menu: MenuDetails_menu | null;
}

export interface MenuDetailsVariables {
  id: string;
}
