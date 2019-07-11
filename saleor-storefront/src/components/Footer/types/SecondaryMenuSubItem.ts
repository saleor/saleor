/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SecondaryMenuSubItem
// ====================================================

export interface SecondaryMenuSubItem_category {
  __typename: "Category";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface SecondaryMenuSubItem_collection {
  __typename: "Collection";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface SecondaryMenuSubItem_page {
  __typename: "Page";
  slug: string;
}

export interface SecondaryMenuSubItem {
  __typename: "MenuItem";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  category: SecondaryMenuSubItem_category | null;
  /**
   * URL to the menu item.
   */
  url: string | null;
  collection: SecondaryMenuSubItem_collection | null;
  page: SecondaryMenuSubItem_page | null;
}
