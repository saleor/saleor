/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: SecondaryMenu
// ====================================================

export interface SecondaryMenu_shop_navigation_secondary_items_category {
  __typename: "Category";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface SecondaryMenu_shop_navigation_secondary_items_collection {
  __typename: "Collection";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface SecondaryMenu_shop_navigation_secondary_items_page {
  __typename: "Page";
  slug: string;
}

export interface SecondaryMenu_shop_navigation_secondary_items_children_category {
  __typename: "Category";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface SecondaryMenu_shop_navigation_secondary_items_children_collection {
  __typename: "Collection";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface SecondaryMenu_shop_navigation_secondary_items_children_page {
  __typename: "Page";
  slug: string;
}

export interface SecondaryMenu_shop_navigation_secondary_items_children {
  __typename: "MenuItem";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  category: SecondaryMenu_shop_navigation_secondary_items_children_category | null;
  /**
   * URL to the menu item.
   */
  url: string | null;
  collection: SecondaryMenu_shop_navigation_secondary_items_children_collection | null;
  page: SecondaryMenu_shop_navigation_secondary_items_children_page | null;
}

export interface SecondaryMenu_shop_navigation_secondary_items {
  __typename: "MenuItem";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  category: SecondaryMenu_shop_navigation_secondary_items_category | null;
  /**
   * URL to the menu item.
   */
  url: string | null;
  collection: SecondaryMenu_shop_navigation_secondary_items_collection | null;
  page: SecondaryMenu_shop_navigation_secondary_items_page | null;
  children: (SecondaryMenu_shop_navigation_secondary_items_children | null)[] | null;
}

export interface SecondaryMenu_shop_navigation_secondary {
  __typename: "Menu";
  items: (SecondaryMenu_shop_navigation_secondary_items | null)[] | null;
}

export interface SecondaryMenu_shop_navigation {
  __typename: "Navigation";
  /**
   * Secondary navigation bar.
   */
  secondary: SecondaryMenu_shop_navigation_secondary | null;
}

export interface SecondaryMenu_shop {
  __typename: "Shop";
  /**
   * Shop's navigation.
   */
  navigation: SecondaryMenu_shop_navigation | null;
}

export interface SecondaryMenu {
  /**
   * Represents a shop resources.
   */
  shop: SecondaryMenu_shop | null;
}
