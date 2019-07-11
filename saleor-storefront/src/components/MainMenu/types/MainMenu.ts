/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: MainMenu
// ====================================================

export interface MainMenu_shop_navigation_main_items_category {
  __typename: "Category";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface MainMenu_shop_navigation_main_items_collection {
  __typename: "Collection";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface MainMenu_shop_navigation_main_items_page {
  __typename: "Page";
  slug: string;
}

export interface MainMenu_shop_navigation_main_items_parent {
  __typename: "MenuItem";
  /**
   * The ID of the object.
   */
  id: string;
}

export interface MainMenu_shop_navigation_main_items_children_category {
  __typename: "Category";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface MainMenu_shop_navigation_main_items_children_collection {
  __typename: "Collection";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface MainMenu_shop_navigation_main_items_children_page {
  __typename: "Page";
  slug: string;
}

export interface MainMenu_shop_navigation_main_items_children_parent {
  __typename: "MenuItem";
  /**
   * The ID of the object.
   */
  id: string;
}

export interface MainMenu_shop_navigation_main_items_children_children_category {
  __typename: "Category";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface MainMenu_shop_navigation_main_items_children_children_collection {
  __typename: "Collection";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface MainMenu_shop_navigation_main_items_children_children_page {
  __typename: "Page";
  slug: string;
}

export interface MainMenu_shop_navigation_main_items_children_children_parent {
  __typename: "MenuItem";
  /**
   * The ID of the object.
   */
  id: string;
}

export interface MainMenu_shop_navigation_main_items_children_children {
  __typename: "MenuItem";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  category: MainMenu_shop_navigation_main_items_children_children_category | null;
  /**
   * URL to the menu item.
   */
  url: string | null;
  collection: MainMenu_shop_navigation_main_items_children_children_collection | null;
  page: MainMenu_shop_navigation_main_items_children_children_page | null;
  parent: MainMenu_shop_navigation_main_items_children_children_parent | null;
}

export interface MainMenu_shop_navigation_main_items_children {
  __typename: "MenuItem";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  category: MainMenu_shop_navigation_main_items_children_category | null;
  /**
   * URL to the menu item.
   */
  url: string | null;
  collection: MainMenu_shop_navigation_main_items_children_collection | null;
  page: MainMenu_shop_navigation_main_items_children_page | null;
  parent: MainMenu_shop_navigation_main_items_children_parent | null;
  children: (MainMenu_shop_navigation_main_items_children_children | null)[] | null;
}

export interface MainMenu_shop_navigation_main_items {
  __typename: "MenuItem";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  category: MainMenu_shop_navigation_main_items_category | null;
  /**
   * URL to the menu item.
   */
  url: string | null;
  collection: MainMenu_shop_navigation_main_items_collection | null;
  page: MainMenu_shop_navigation_main_items_page | null;
  parent: MainMenu_shop_navigation_main_items_parent | null;
  children: (MainMenu_shop_navigation_main_items_children | null)[] | null;
}

export interface MainMenu_shop_navigation_main {
  __typename: "Menu";
  /**
   * The ID of the object.
   */
  id: string;
  items: (MainMenu_shop_navigation_main_items | null)[] | null;
}

export interface MainMenu_shop_navigation {
  __typename: "Navigation";
  /**
   * Main navigation bar.
   */
  main: MainMenu_shop_navigation_main | null;
}

export interface MainMenu_shop {
  __typename: "Shop";
  /**
   * Shop's navigation.
   */
  navigation: MainMenu_shop_navigation | null;
}

export interface MainMenu {
  /**
   * Represents a shop resources.
   */
  shop: MainMenu_shop | null;
}
